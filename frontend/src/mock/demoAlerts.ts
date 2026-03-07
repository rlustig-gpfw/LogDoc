import { Alert } from '@/types'

export const INITIAL_ALERTS: Alert[] = [
  {
    id: 'alert-001',
    title: 'SSH Brute Force Detected',
    timestamp: '10:42:15',
    severity: 'high',
    status: 'new',
    source_ip: '185.12.44.9',
    dest_ip: '10.0.2.15',
    description: 'Repeated failed SSH authentication attempts from external IP.',
    raw_log: `ts=1712334031.412 uid=Cq1kFf2a7bZXkT3Rk id.orig_h=185.12.44.9 id.orig_p=53291 id.resp_h=10.0.2.15 id.resp_p=22 proto=tcp service=ssh conn_state=RSTO history=ShADadfr orig_bytes=1840 resp_bytes=2420
ts=1712334033.120 uid=Cv2mGh3b8cYWlU4Sl id.orig_h=185.12.44.9 id.orig_p=53292 id.resp_h=10.0.2.15 id.resp_p=22 proto=tcp service=ssh conn_state=RSTO history=ShADadfr orig_bytes=1840 resp_bytes=2420
ts=1712334034.875 uid=Cw3nHi4c9dZXmV5Tm id.orig_h=185.12.44.9 id.orig_p=53293 id.resp_h=10.0.2.15 id.resp_p=22 proto=tcp service=ssh conn_state=RSTO history=ShADadfr orig_bytes=1840 resp_bytes=2420
ts=1712334036.224 uid=Cx4oIj5d0eAYnW6Un id.orig_h=185.12.44.9 id.orig_p=53294 id.resp_h=10.0.2.15 id.resp_p=22 proto=tcp service=ssh conn_state=RSTO history=ShADadfr orig_bytes=1840 resp_bytes=2420
ts=1712334037.891 uid=Cy5pJk6e1fBZoX7Vo id.orig_h=185.12.44.9 id.orig_p=53295 id.resp_h=10.0.2.15 id.resp_p=22 proto=tcp service=ssh conn_state=RSTO history=ShADadfr orig_bytes=1840 resp_bytes=2420
ts=1712334039.332 uid=Cz6qKl7f2gCAoY8Wp id.orig_h=185.12.44.9 id.orig_p=53296 id.resp_h=10.0.2.15 id.resp_p=22 proto=tcp service=ssh conn_state=RSTO history=ShADadfr orig_bytes=1840 resp_bytes=2420
ts=1712334041.015 uid=Da7rLm8g3hDBpZ9Xq id.orig_h=185.12.44.9 id.orig_p=53297 id.resp_h=10.0.2.15 id.resp_p=22 proto=tcp service=ssh conn_state=RSTO history=ShADadfr orig_bytes=1840 resp_bytes=2420`,
  },
  {
    id: 'alert-002',
    title: 'DNS Tunneling Suspected',
    timestamp: '09:17:44',
    severity: 'medium',
    status: 'triaged',
    source_ip: '10.0.1.42',
    dest_ip: '8.8.8.8',
    description: 'Unusually long DNS query strings suggesting data exfiltration via DNS.',
    raw_log: `ts=1712330264.001 uid=Ce1aAb2c3dEFgHi4j id.orig_h=10.0.1.42 id.orig_p=52341 id.resp_h=8.8.8.8 id.resp_p=53 proto=udp service=dns query=aGVsbG8td29ybGQtdGhpcy1pcy1hLXZlcnktbG9uZy1zdWJkb21haW4tZm9yLXRlc3RpbmctcHVycG9zZXM=.evil-domain.com qtype_name=TXT rcode_name=NOERROR
ts=1712330265.234 uid=Cf2bBc3d4eGHiJk5l id.orig_h=10.0.1.42 id.orig_p=52342 id.resp_h=8.8.8.8 id.resp_p=53 proto=udp service=dns query=dGhpcy1pcy1tb3JlLXRlc3QtZGF0YS10aGF0LWxvb2tzLXN1c3BpY2lvdXM=.evil-domain.com qtype_name=TXT rcode_name=NOERROR
ts=1712330266.891 uid=Cg3cCd4e5fHIjKl6m id.orig_h=10.0.1.42 id.orig_p=52343 id.resp_h=8.8.8.8 id.resp_p=53 proto=udp service=dns query=ZXhmaWx0cmF0aW9uLWRhdGEtY2h1bmsz.evil-domain.com qtype_name=TXT rcode_name=NOERROR`,
  },
  {
    id: 'alert-003',
    title: 'Internal Port Scan',
    timestamp: '08:55:02',
    severity: 'medium',
    status: 'new',
    source_ip: '10.0.0.88',
    dest_ip: '10.0.0.0/24',
    description: 'Host scanning multiple internal IPs across common service ports.',
    raw_log: `ts=1712329102.441 uid=Ch4dDe5f6gIJkLm7n id.orig_h=10.0.0.88 id.orig_p=60001 id.resp_h=10.0.0.1 id.resp_p=22 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712329102.445 uid=Ci5eEf6g7hJKlMn8o id.orig_h=10.0.0.88 id.orig_p=60002 id.resp_h=10.0.0.2 id.resp_p=22 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712329102.447 uid=Cj6fFg7h8iKLmNo9p id.orig_h=10.0.0.88 id.orig_p=60003 id.resp_h=10.0.0.3 id.resp_p=80 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712329102.449 uid=Ck7gGh8i9jLMnOp0q id.orig_h=10.0.0.88 id.orig_p=60004 id.resp_h=10.0.0.4 id.resp_p=443 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712329102.452 uid=Cl8hHi9j0kMNoPq1r id.orig_h=10.0.0.88 id.orig_p=60005 id.resp_h=10.0.0.5 id.resp_p=3389 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712329102.455 uid=Cm9iIj0k1lNOpQr2s id.orig_h=10.0.0.88 id.orig_p=60006 id.resp_h=10.0.0.6 id.resp_p=445 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0`,
  },
  {
    id: 'alert-004',
    title: 'Suspicious HTTP Exfiltration',
    timestamp: '08:22:18',
    severity: 'high',
    status: 'escalated',
    source_ip: '10.0.1.77',
    dest_ip: '203.0.113.50',
    description: 'Large outbound HTTP POST to unknown external IP with encoded payload.',
    raw_log: `ts=1712327938.123 uid=Cn0jJk1l2mOPqRs3t id.orig_h=10.0.1.77 id.orig_p=49201 id.resp_h=203.0.113.50 id.resp_p=80 proto=tcp service=http method=POST uri=/upload/data host=203.0.113.50 user_agent=Mozilla/5.0 request_body_len=524288 response_body_len=42 status_code=200
ts=1712327940.445 uid=Co1kKl2m3nPQrSt4u id.orig_h=10.0.1.77 id.orig_p=49202 id.resp_h=203.0.113.50 id.resp_p=80 proto=tcp service=http method=POST uri=/upload/data2 host=203.0.113.50 user_agent=Mozilla/5.0 request_body_len=524288 response_body_len=42 status_code=200`,
  },
  {
    id: 'alert-005',
    title: 'Benign Web Browsing',
    timestamp: '07:44:31',
    severity: 'low',
    status: 'resolved',
    source_ip: '10.0.1.10',
    dest_ip: '142.250.80.46',
    description: 'Normal HTTPS traffic to known CDN endpoints.',
    raw_log: `ts=1712325871.001 uid=Cp2lLm3n4oQRsT5u id.orig_h=10.0.1.10 id.orig_p=55210 id.resp_h=142.250.80.46 id.resp_p=443 proto=tcp service=ssl conn_state=SF history=ShADadfFr orig_bytes=4210 resp_bytes=82940
ts=1712325872.334 uid=Cq3mMn4o5pRSaT6v id.orig_h=10.0.1.10 id.orig_p=55211 id.resp_h=142.250.80.46 id.resp_p=443 proto=tcp service=ssl conn_state=SF history=ShADadfFr orig_bytes=3102 resp_bytes=61240`,
  },
]

export const DEMO_STREAM_ALERT: Alert = {
  id: `alert-demo-${Date.now()}`,
  title: 'Port Scan (Reconnaissance)',
  timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
  severity: 'high',
  status: 'new',
  source_ip: '192.168.1.55',
  dest_ip: '10.0.0.0/16',
  description: 'Systematic port scanning activity across the internal network subnet.',
  raw_log: `ts=1712334900.001 uid=Dr1aAb2c3dEFgHi4j id.orig_h=192.168.1.55 id.orig_p=41000 id.resp_h=10.0.0.1 id.resp_p=21 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.003 uid=Ds2bBc3d4eGHiJk5l id.orig_h=192.168.1.55 id.orig_p=41001 id.resp_h=10.0.0.1 id.resp_p=22 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.005 uid=Dt3cCd4e5fHIjKl6m id.orig_h=192.168.1.55 id.orig_p=41002 id.resp_h=10.0.0.1 id.resp_p=23 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.007 uid=Du4dDe5f6gIJkLm7n id.orig_h=192.168.1.55 id.orig_p=41003 id.resp_h=10.0.0.1 id.resp_p=80 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.009 uid=Dv5eEf6g7hJKlMn8o id.orig_h=192.168.1.55 id.orig_p=41004 id.resp_h=10.0.0.1 id.resp_p=443 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.011 uid=Dw6fFg7h8iKLmNo9p id.orig_h=192.168.1.55 id.orig_p=41005 id.resp_h=10.0.0.1 id.resp_p=3306 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.013 uid=Dx7gGh8i9jLMnOp0q id.orig_h=192.168.1.55 id.orig_p=41006 id.resp_h=10.0.0.1 id.resp_p=5432 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.015 uid=Dy8hHi9j0kMNoPq1r id.orig_h=192.168.1.55 id.orig_p=41007 id.resp_h=10.0.0.2 id.resp_p=21 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.017 uid=Dz9iIj0k1lNOpQr2s id.orig_h=192.168.1.55 id.orig_p=41008 id.resp_h=10.0.0.2 id.resp_p=22 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0
ts=1712334900.019 uid=Ea0jJk1l2mOPqRs3t id.orig_h=192.168.1.55 id.orig_p=41009 id.resp_h=10.0.0.2 id.resp_p=80 proto=tcp conn_state=S0 history=S orig_bytes=0 resp_bytes=0`,
}

export function createDemoAlert(): Alert {
  return {
    ...DEMO_STREAM_ALERT,
    id: `alert-demo-${Date.now()}`,
    timestamp: new Date().toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
  }
}
