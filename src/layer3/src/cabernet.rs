use crate::error::{CabernetError, Result};
use crate::ue::UE;
use pyo3::{pyclass, pymethods};

/// Cabernet is responsible for spinning up the UEs and proxy the network layer traffic between UEs
/// and the underlying implementation (e.g., a 5G core network).
#[pyclass]
pub struct Cabernet {
    pub ues: Vec<UE>,
    pub gateway: Option<UE>,
}

/// APIs
#[pymethods]
impl Cabernet {
    #[new]
    pub fn new() -> Self {
        Cabernet {
            ues: Vec::new(),
            gateway: None,
        }
    }

    #[staticmethod]
    pub fn with_internet(gateway: &str, subnet: &str) -> Result<Self> {
        let gw_ue = UE::with_gateway(gateway.into(), subnet);

        Ok(Self {
            ues: Vec::new(),
            gateway: Some(gw_ue),
        })
    }

    /// Send an IPv4 frame to the appropriate UE based on the destination IP address in the frame.
    /// If gateway is configured, send to gateway if no matching UE is found.
    pub fn send_frame(&self, frame: Vec<u8>) -> Result<usize> {
        let iph = etherparse::Ipv4HeaderSlice::from_slice(&frame)?;
        let dst_ip = iph.destination_addr().to_string();

        match self.get_ue(&dst_ip) {
            Ok(ue) => ue.send(&frame),
            Err(e) => match &self.gateway {
                Some(gw) => gw.send(&frame),
                None => Err(e),
            },
        }
    }

    /// Poll an IPv4 frame received from any UE.
    /// Returns None if no frame is available.
    pub fn poll_frame(&mut self) -> Option<Vec<u8>> {
        fn poll(ue: &mut UE) -> Option<Vec<u8>> {
            match ue.recv() {
                Ok(Some(buf)) => Some(buf),
                Ok(None) => None,
                Err(e) => {
                    eprintln!("Error receiving from from UE {}: {}", ue.ip, e);
                    None
                }
            }
        }
        self.ues
            .iter_mut()
            .chain(self.gateway.iter_mut())
            .find_map(poll)
    }

    pub fn poll_frame_from_ue(&mut self, ip: &str) -> Result<Option<Vec<u8>>> {
        self.get_ue(ip)?.recv()
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
            .chain(self.gateway.iter())
            .find(|ue| ue.ip == ip)
            .ok_or(CabernetError::IPNotAssigned(ip.into()))
    }
}
