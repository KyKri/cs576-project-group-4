use crate::error::Result;
use nix::libc;
use nix::sched::{clone, setns, CloneFlags};
use nix::sys::wait::waitpid;
use nix::unistd::{getpid, Pid};
use std::process::Command;

const STACK_SIZE: usize = 1024 * 1024; // 1 MB stack for child

pub struct UE {
    pub ip: String,
    pub iface: tun_tap::Iface,
    pub pause_pid: Pid,
}

impl UE {
    pub fn new(ip: String) -> Self {
        // create pause process in new netns
        let pause_pid = create_pause();

        // attach netns to the ip netns list (for better visibility)
        attach_netns(pause_pid);

        // create and setup tun in that netns
        let iface = create_tun(pause_pid, &ip);

        Self {
            ip,
            iface,
            pause_pid,
        }
    }

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

    pub fn recv(&self, buf: &mut [u8]) -> Result<usize> {
        self.iface.recv(buf).map_err(Into::into)
    }
}

fn attach_netns(pause_pid: Pid) {
    // ip netns attach childns {pause_pid}
    let output = Command::new("ip")
        .args(format!("netns attach ana-{pause_pid} {pause_pid}").split(' '))
        .output()
        .expect("failed to execute process");
    if !output.status.success() {
        eprintln!(
            "Error attaching netns: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

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
    let tun = tun_tap::Iface::without_packet_info(&format!("ana-{cid}"), tun_tap::Mode::Tun).unwrap();
    setup_tun(&tun, ip);
    // go back to original ns
    setns(org_ns_fd, nix::sched::CloneFlags::CLONE_NEWNET).unwrap();

    tun
}

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

fn setup_default_route(tun: &tun_tap::Iface, ip: &str) {
    let output = Command::new("ip")
        .args(format!("r add default via {ip} dev {}", &tun.name()).split(' '))
        .output()
        .expect("failed to execute process");

    if !output.status.success() {
        eprintln!(
            "Error routing default gateway to ip: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

fn setup_tun(tun: &tun_tap::Iface, ip: &str) {
    assign_ip_to_tun(tun, ip);
    bring_interface_up(tun);
    setup_default_route(tun, ip);
}

impl Drop for UE {
    fn drop(&mut self) {
        // kill pause process
        let _ = nix::sys::signal::kill(self.pause_pid, nix::sys::signal::Signal::SIGKILL);
        // wait for pause process to exit
        let _ = waitpid(self.pause_pid, None).expect("waitpid failed");
    }
}
