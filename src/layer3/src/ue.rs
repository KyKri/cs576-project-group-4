use crate::error::Result;
use nix::libc;
use nix::sched::{clone, setns, CloneFlags};
use nix::sys::wait::waitpid;
use nix::unistd::{getpid, Pid};
use pyo3::{pyclass, pymethods};
use std::io::{Read, Write};
use std::process::Command;

const STACK_SIZE: usize = 1024 * 1024; // 1 MB stack for child

/// Representation of a User Equipment (UE)
/// Each UE has its own network namespace with a TUN interface which is used to route the entire
/// network traffic to/from the UE.
#[derive(Debug)]
#[pyclass]
pub struct UE {
    /// IP address assigned to the UE
    pub ip: String,
    /// TUN interface associated with the UE
    pub iface: tun_tap::Iface,
    /// PID of the pause process running in the UE's network namespace
    pub pause_pid: Pid,
}

impl UE {
    /// Create a new UE with the specified IP address
    pub fn new(ip: String) -> Self {
        // create pause process in new netns
        let pause_pid = create_pause();

        // attach netns to the ip netns list (for better visibility)
        attach_netns(pause_pid, &ip);

        // create and setup tun in that netns
        let iface = create_tun(pause_pid, &ip);

        // setup default route via the given ip
        setup_default_route(&iface, &ip);

        Self {
            ip,
            iface,
            pause_pid,
        }
    }
    pub fn with_gateway(ip: String, subnet: &str) -> Self {
        // create pause process in new netns
        let pause_pid = create_pause();

        // attach netns to the ip netns list (for better visibility)
        attach_netns(pause_pid, &ip);

        // create and setup tun in that netns
        let iface = create_tun(pause_pid, &ip);

        // setup internet access via the given gateway
        setup_internet_access(&ip, subnet);

        Self {
            ip,
            iface,
            pause_pid,
        }
    }
}

#[pymethods]
impl UE {
    /// Change the IP address assigned to the UE
    pub fn change_ip(&self, new_ip: String) {
        assign_ip_to_tun(&self.iface, &new_ip);
        setup_default_route(&self.iface, &new_ip);
    }

    /// Send IPv4 frames to the UE
    /// data is assumed to be the raw IPv4 packet (without Ethernet header)
    /// MTU is assumed to be 1500 bytes
    pub fn send(&self, data: &[u8]) -> Result<usize> {
        self.iface.send(data).map_err(Into::into)
    }

    /// Receive IPv4 frames from the UE
    /// data is assumed to be the raw IPv4 packet (without Ethernet header)
    /// MTU is assumed to be 1500 bytes
    pub fn recv(&self) -> Result<Option<Vec<u8>>> {
        let mut buf = [0u8; 1500];
        match self.iface.recv(&mut buf) {
            Ok(nbytes) => match etherparse::Ipv4HeaderSlice::from_slice(&buf[..nbytes]) {
                Ok(_) => Ok(Some(buf[..nbytes].to_vec())),
                Err(e) => {
                    // eprintln!("Failed to parse IPv4 header: {e}");
                    Ok(None)
                }
            },
            Err(e) => match e.kind() {
                std::io::ErrorKind::WouldBlock => Ok(None),
                _ => Err(e),
            },
        }
        .map_err(Into::into)
    }
}

/// Attach the network namespace of the pause process to the ip netns list
fn attach_netns(pause_pid: Pid, ip: &str) {
    // ip netns attach childns {pause_pid}
    let output = Command::new("ip")
        .args(format!("netns attach {} {pause_pid}", netns_for_ip(ip)).split(' '))
        .output()
        .expect("failed to execute process");
    if !output.status.success() {
        eprintln!(
            "Error attaching netns: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

/// Detach the network namespace of the pause process from the ip netns list
fn detach_netns(ip: &str) {
    // ip netns delete childns
    let output = Command::new("ip")
        .args(format!("netns delete {}", netns_for_ip(ip)).split(' '))
        .output()
        .expect("failed to execute process");
    if !output.status.success() {
        eprintln!(
            "Error detaching netns: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

/// Create a pause process in a new network namespace
pub fn create_pause() -> Pid {
    // allocating the stack
    let mut stack: Vec<u8> = Vec::with_capacity(STACK_SIZE);
    #[allow(clippy::uninit_vec)]
    unsafe {
        stack.set_len(STACK_SIZE)
    };
    let stack_top = stack.as_mut();

    let child_func = Box::new(|| -> isize { unsafe { nix::libc::pause() as isize } });

    unsafe {
        clone(
            child_func,
            stack_top,
            CloneFlags::CLONE_NEWNET,
            Some(libc::SIGCHLD),
        )
        .expect("clone failed")
    }
}

/// Create and setup a TUN interface in the network namespace of the given PID
fn create_tun(cid: Pid, ip: &str) -> tun_tap::Iface {
    // set ns into cid's nn
    let new_ns_fd = nix::fcntl::open(
        &std::path::PathBuf::from(format!("/proc/{cid}/ns/net")),
        nix::fcntl::OFlag::O_RDONLY,
        nix::sys::stat::Mode::empty(),
    )
    .unwrap();

    let pid = getpid();
    let org_ns_fd = nix::fcntl::open(
        &std::path::PathBuf::from(format!("/proc/{pid}/ns/net")),
        nix::fcntl::OFlag::O_RDONLY,
        nix::sys::stat::Mode::empty(),
    )
    .unwrap();

    setns(new_ns_fd, nix::sched::CloneFlags::CLONE_NEWNET).unwrap();

    // create tun
    let tun =
        tun_tap::Iface::without_packet_info(&format!("cab-{cid}"), tun_tap::Mode::Tun).unwrap();
    tun.set_non_blocking().unwrap();
    setup_tun(&tun, ip);

    // go back to original ns
    setns(org_ns_fd, nix::sched::CloneFlags::CLONE_NEWNET).unwrap();

    tun
}

/// Assign an IP address to the TUN interface
fn assign_ip_to_tun(tun: &tun_tap::Iface, ip: &str) {
    let output = Command::new("ip")
        .args(format!("addr add {ip}/24 dev {}", &tun.name()).split(' '))
        .output()
        .expect("failed to execute process");
    if !output.status.success() {
        eprintln!(
            "Error adding IP address: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

/// Bring the TUN interface up
fn bring_interface_up(tun: &tun_tap::Iface) {
    let output = Command::new("ip")
        .args(format!("link set dev {} up", &tun.name()).split(' '))
        .output()
        .expect("failed to execute process");
    if !output.status.success() {
        eprintln!(
            "Error setting interface up: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

/// Setup the default route via the TUN interface
fn setup_default_route(tun: &tun_tap::Iface, ip: &str) {
    let output = Command::new("ip")
        .args(
            format!(
                "-n {} r add default via {ip} dev {}",
                netns_for_ip(ip),
                &tun.name()
            )
            .split(' '),
        )
        .output()
        .expect("failed to execute process");

    if !output.status.success() {
        eprintln!(
            "Error routing default gateway to ip: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

/// Setup the TUN interface with the given IP address
fn setup_tun(tun: &tun_tap::Iface, ip: &str) {
    assign_ip_to_tun(tun, ip);
    bring_interface_up(tun);
}

/// Setup internet access on the UE for the given subnet
fn setup_internet_access(ip: &str, subnet: &str) {
    const SCRIPT: &str = include_str!("../scripts/setup_internet.sh");

    let mut child = Command::new("bash")
        .args(["-s", "--", &netns_for_ip(ip), subnet])
        .stdin(std::process::Stdio::piped())
        .spawn()
        .expect("failed to spawn bash for internet setup");

    {
        let stdin = child.stdin.as_mut().expect("failed to open stdin");
        stdin
            .write_all(SCRIPT.as_bytes())
            .expect("failed to write internet setup script to stdin");
    }

    let status = child.wait().expect("failed to wait on child");

    if !status.success() {
        let mut buf = String::new();
        let _nbytes = &child
            .stderr
            .expect("failed to get stderr")
            .read_to_string(&mut buf)
            .unwrap();
        eprintln!("Error setting up internet access: {buf}",);
    }
}

fn netns_for_ip(ip: &str) -> String {
    format!("cab-{}", ip)
}

impl Drop for UE {
    fn drop(&mut self) {
        eprintln!("Dropping UE with IP {}", self.ip);
        // remove netns from ip netns list
        detach_netns(&self.ip);
        // kill pause process
        let _ = nix::sys::signal::kill(self.pause_pid, nix::sys::signal::Signal::SIGKILL);
        // wait for pause process to exit
        let _ = waitpid(self.pause_pid, None).expect("waitpid failed");
    }
}
