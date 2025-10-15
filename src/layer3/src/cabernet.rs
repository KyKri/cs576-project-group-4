use std::sync::Arc;

use crate::error::{CabernetError, Result};
use crate::ue::UE;

pub struct Cabernet {
    pub ues: Vec<Arc<UE>>,
    pub buffer: Arc<crossbeam::queue::SegQueue<Vec<u8>>>,
    pub threads: Vec<std::thread::JoinHandle<()>>,
}

// APIs
impl Cabernet {
    pub fn new() -> Self {
        Cabernet {
            ues: Vec::new(),
            buffer: Arc::new(crossbeam::queue::SegQueue::new()),
            threads: Vec::new(),
        }
    }

    pub fn send_frame(&self, frame: Vec<u8>) -> Result<usize> {
        let iph = etherparse::Ipv4HeaderSlice::from_slice(&frame)?;
        let dst_ip = iph.destination_addr().to_string();

        Ok(self.get_ue(&dst_ip)?.send(&frame))
    }

    pub fn poll_frame(&mut self) -> Option<Vec<u8>> {
        self.buffer.pop().map(|b| b.to_vec())
    }

    pub fn create_ue(&mut self, ip: String) -> Result<()> {
        let ue = UE::new(ip);
        self.ues.push(Arc::new(ue));
        let j = self.poll_from_ue(self.ues.len() - 1);
        self.threads.push(j);
        Ok(())
    }

    pub fn change_ip(&mut self, old_ip: String, new_ip: String) -> Result<()> {
        self.get_ue(&old_ip)?.change_ip(new_ip);
        Ok(())
    }

    fn get_ue(&self, ip: &str) -> Result<Arc<UE>> {
        self.ues
            .iter()
            .find(|ue| ue.ip == ip)
            .ok_or(CabernetError::IPNotAssignedError)
            .map(Arc::clone)
    }

    fn poll_from_ue(&self, ue_id: usize) -> std::thread::JoinHandle<()> {
        let ue = &self.ues[ue_id];
        let ue = Arc::clone(ue);
        let buffer = Arc::clone(&self.buffer);
        std::thread::spawn(move || loop {
            let mut buf = Vec::with_capacity(1500);
            let _nbytes = ue.recv(&mut buf);
            buffer.push(buf);
        })
    }
}
