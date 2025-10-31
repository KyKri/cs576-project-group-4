use std::sync::Arc;

use crate::error::{CabernetError, Result};
use crate::ue::UE;
use pyo3::{pyclass, pymethods};

/// Cabernet is responsible for spinning up the UEs and proxy the network layer traffic between UEs
/// and the underlying implementation (e.g., a 5G core network).
#[pyclass]
pub struct Cabernet {
    /// List of UEs managed by the Cabernet instance
    pub ues: Vec<Arc<UE>>,
    /// A queue of received ip frams from all UEs
    buffer: Arc<crossbeam::queue::SegQueue<Vec<u8>>>,
    /// Threads polling frames from UEs
    threads: Vec<std::thread::JoinHandle<()>>,
}

/// APIs
#[pymethods]
impl Cabernet {
    #[new]
    pub fn new() -> Self {
        Cabernet {
            ues: Vec::new(),
            buffer: Arc::new(crossbeam::queue::SegQueue::new()),
            threads: Vec::new(),
        }
    }

    /// Send an IPv4 frame to the appropriate UE based on the destination IP address in the frame.
    pub fn send_frame(&self, frame: Vec<u8>) -> Result<usize> {
        let iph = etherparse::Ipv4HeaderSlice::from_slice(&frame)?;
        let dst_ip = iph.destination_addr().to_string();

        self.get_ue(&dst_ip)?.send(&frame)
    }

    /// Poll an IPv4 frame received from any UE.
    /// Returns None if no frame is available.
    pub fn poll_frame(&mut self) -> Option<Vec<u8>> {
        self.buffer.pop().map(|b| b.to_vec())
    }

    /// Create a new UE with the specified IP address and start polling frames from it.
    pub fn create_ue(&mut self, ip: &str) -> Result<()> {
        let ue = UE::new(ip.into());
        self.ues.push(Arc::new(ue));
        let j = self.poll_from_ue(self.ues.len() - 1);
        self.threads.push(j);
        Ok(())
    }

    /// Change the IP address assigned to a UE.
    pub fn change_ip(&mut self, old_ip: String, new_ip: String) -> Result<()> {
        self.get_ue(&old_ip)?.change_ip(new_ip);
        Ok(())
    }
}

impl Default for Cabernet {
    fn default() -> Self {
        Self::new()
    }
}

impl Cabernet {
    fn get_ue(&self, ip: &str) -> Result<Arc<UE>> {
        self.ues
            .iter()
            .find(|ue| ue.ip == ip)
            .ok_or(CabernetError::IPNotAssigned(ip.into()))
            .map(Arc::clone)
    }

    pub fn poll_from_ue(&self, ue_id: usize) -> std::thread::JoinHandle<()> {
        let ue = Arc::clone(&self.ues[ue_id]);
        let buffer = Arc::clone(&self.buffer);
        std::thread::spawn(move || loop {
            let mut buf = [0u8; 1500];
            let nbytes = ue.recv(&mut buf).unwrap();

            match etherparse::Ipv4HeaderSlice::from_slice(&buf[..nbytes]) {
                Ok(_) => buffer.push(buf[..nbytes].to_vec()),
                Err(e) => eprintln!("Failed to parse IPv4 header: {e}"),
            }
        })
    }
}
