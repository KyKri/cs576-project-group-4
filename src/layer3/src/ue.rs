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

        // create and setup tun in that netns
        let iface = create_tun(pause_pid, &ip);

        Self {
            ip,
            iface,
            pause_pid,
        }
    }

    pub fn change_ip(&mut self, new_ip: String) {
        assign_ip_to_tun(&self.iface, &new_ip);
        setup_default_route(&self.iface, &new_ip);
    }

    pub fn send(&self, data: &[u8]) -> usize {
        self.iface.send(data).expect("Failed to send data")
    }

    pub fn recv(&self, buf: &mut [u8]) -> usize {
        self.iface.recv(buf).expect("Failed to receive data")
    }
}

pub fn create_pause() -> Pid {
    // allocating the stack
    let mut stack: Vec<u8> = Vec::with_capacity(STACK_SIZE);
    unsafe { stack.set_len(STACK_SIZE) };
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
    let tun = tun_tap::Iface::new(&format!("ana-{cid}"), tun_tap::Mode::Tun).unwrap();
    setup_tun(&tun, ip);
    // go back to original ns
    setns(org_ns_fd, nix::sched::CloneFlags::CLONE_NEWNET).unwrap();

    tun
}

fn assign_ip_to_tun(tun: &tun_tap::Iface, ip: &str) {
    //ip addr add 10.10.0.1/32 dev tun0
    let output = Command::new("ip")
        .args(format!("addr add {ip} dev {}", &tun.name()).split(' '))
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
    // ip link set tun0 up
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
    // ip r add default via {ip} {iface.name()}
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
