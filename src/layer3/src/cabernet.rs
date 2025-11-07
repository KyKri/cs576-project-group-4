use crate::error::{CabernetError, Result};
use crate::ue::UE;
use pyo3::{pyclass, pymethods};

/// Cabernet is responsible for spinning up the UEs and proxy the network layer traffic between UEs
/// and the underlying implementation (e.g., a 5G core network).
#[pyclass]
pub struct Cabernet {
    pub ues: Vec<UE>,
}

/// APIs
#[pymethods]
impl Cabernet {
    #[new]
    pub fn new() -> Self {
        Cabernet { ues: Vec::new() }
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
        // self.buffer.pop().map(|b| b.to_vec())
        for ue in &mut self.ues {
            let mut buf = [0u8; 1500];
            match ue.recv(&mut buf) {
                Ok(Some(nbytes)) => return Some(buf[..nbytes].to_vec()),
                Ok(None) => continue,
                Err(e) => {
                    eprintln!("Error receiving frame from UE {}: {}", ue.ip, e);
                    continue;
                }
            }
        }
        None
    }

    /// Create a new UE with the specified IP address and start polling frames from it.
    pub fn create_ue(&mut self, ip: &str) -> Result<()> {
        let ue = UE::new(ip.into());
        self.ues.push(ue);
        Ok(())
    }

    /// Delete the UE with the specified IP address.
    pub fn delete_ue(&mut self, ip: &str) -> Result<()> {
        dbg!(&self.ues);
        let index = self
            .ues
            .iter()
            .position(|ue| ue.ip == ip)
            .ok_or(CabernetError::IPNotAssigned(ip.into()))?;
        let _ue = self.ues.remove(index);
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
    // fn get_ue(&self, ip: &str) -> Result<Arc<UE>> {
    fn get_ue(&self, ip: &str) -> Result<&UE> {
        self.ues
            .iter()
            .find(|ue| ue.ip == ip)
            .ok_or(CabernetError::IPNotAssigned(ip.into()))
    }
}
