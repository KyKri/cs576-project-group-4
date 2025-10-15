use crate::error::{CabernetError, Result};
use crate::ue::UE;
use std::collections::VecDeque;

pub struct Cabernet {
    pub ues: Vec<UE>,
    pub buffer: VecDeque<[u8; 1500]>,
}

impl Cabernet {
    pub fn new() -> Self {
        Cabernet { ues: Vec::new(), buffer: VecDeque::new() }
    }

    pub fn send_frame(&self, frame: Vec<u8>) -> Result<usize> {
        let iph = etherparse::Ipv4HeaderSlice::from_slice(&frame)?;
        let dst_ip = iph.destination_addr().to_string();

        Ok(self.get_ue(&dst_ip)?.send(&frame))
    }

    pub fn poll_frame(&mut self) -> Option<Vec<u8>> {
        self.buffer.pop_front().map(|b| b.to_vec())
    }

    pub fn create_ue(&mut self, ip: String) -> Result<()> {
        let ue = UE::new(ip);
        self.ues.push(ue);
        Ok(())
    }

    pub fn change_ip(&mut self, old_ip: String, new_ip: String) -> Result<()> {
        self.get_ue_mut(&old_ip)?.change_ip(new_ip);
        Ok(())
    }

    fn get_ue_mut(&mut self, ip: &str) -> Result<&mut UE> {
        self.ues
            .iter_mut()
            .find(|ue| ue.ip == ip)
            .ok_or(CabernetError::IPNotAssignedError)
    }

    fn get_ue(&self, ip: &str) -> Result<&UE> {
        self.ues
            .iter()
            .find(|ue| ue.ip == ip)
            .ok_or(CabernetError::IPNotAssignedError)
    }
}
