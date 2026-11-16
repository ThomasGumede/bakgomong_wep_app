/* Fictional seed data. All records are illustrative, not sourced from a live Bakgomong database. */
window.BAKGOMONG_SEED = {
  // profile: { name: 'Naledi Mokoena', email:'naledi@example.com', role: 'Family Administrator', initials: 'NM' },
  families: [
    { id:'F01', name:'Mokoena Family', branch:'Main Branch', location:'Johannesburg, Gauteng', head:'Thabo Mokoena', members:28, created:'12 Feb 2024', tone:'mint' },
    { id:'F02', name:'Molefe Family', branch:'Northern Branch', location:'Polokwane, Limpopo', head:'Lerato Molefe', members:21, created:'24 Apr 2024', tone:'peach' },
    { id:'F03', name:'Nkosi Family', branch:'Eastern Branch', location:'Durban, KwaZulu-Natal', head:'Sibusiso Nkosi', members:34, created:'03 Jun 2024', tone:'lavender' },
    { id:'F04', name:'Dlamini Family', branch:'Western Branch', location:'Rustenburg, North West', head:'Nomsa Dlamini', members:19, created:'18 Aug 2024', tone:'blue' },
  ],
  members: [
    {id:'M001', name:'Thabo Mokoena', email:'thabo@example.com', phone:'072 000 0111', family:'Mokoena Family', role:'Family Head', status:'Active', joined:'12 Feb 2024'},
    {id:'M002', name:'Naledi Mokoena', email:'naledi@example.com', phone:'072 000 0112', family:'Mokoena Family', role:'Administrator', status:'Active', joined:'14 Feb 2024'},
    {id:'M003', name:'Lerato Molefe', email:'lerato@example.com', phone:'072 000 0113', family:'Molefe Family', role:'Family Head', status:'Active', joined:'24 Apr 2024'},
    {id:'M004', name:'Sibusiso Nkosi', email:'sibusiso@example.com', phone:'072 000 0114', family:'Nkosi Family', role:'Family Head', status:'Active', joined:'03 Jun 2024'},
    {id:'M005', name:'Nomsa Dlamini', email:'nomsa@example.com', phone:'072 000 0115', family:'Dlamini Family', role:'Family Head', status:'Active', joined:'18 Aug 2024'},
    {id:'M006', name:'Kagiso Mokoena', email:'kagiso@example.com', phone:'072 000 0116', family:'Mokoena Family', role:'Member', status:'Active', joined:'21 Sep 2024'},
    {id:'M007', name:'Bontle Molefe', email:'bontle@example.com', phone:'072 000 0117', family:'Molefe Family', role:'Member', status:'Pending', joined:'11 Oct 2024'},
    {id:'M008', name:'Ayanda Nkosi', email:'ayanda@example.com', phone:'072 000 0118', family:'Nkosi Family', role:'Member', status:'Active', joined:'18 Oct 2024'},
    {id:'M009', name:'Tshepo Dlamini', email:'tshepo@example.com', phone:'072 000 0119', family:'Dlamini Family', role:'Member', status:'Inactive', joined:'01 Nov 2024'},
    {id:'M010', name:'Refilwe Mokoena', email:'refilwe@example.com', phone:'072 000 0120', family:'Mokoena Family', role:'Member', status:'Active', joined:'04 Nov 2024'},
  ],
  contributions: [
    {id:'CT-1048', member:'Thabo Mokoena', purpose:'Annual family contribution', family:'Mokoena Family', amount:650, due:'2026-11-30', status:'Paid'},
    {id:'CT-1049', member:'Naledi Mokoena', purpose:'Annual family contribution', family:'Mokoena Family', amount:650, due:'2026-11-30', status:'Paid'},
    {id:'CT-1050', member:'Lerato Molefe', purpose:'Community development fund', family:'Molefe Family', amount:450, due:'2026-11-30', status:'Pending'},
    {id:'CT-1051', member:'Sibusiso Nkosi', purpose:'Annual family contribution', family:'Nkosi Family', amount:650, due:'2026-11-30', status:'Paid'},
    {id:'CT-1052', member:'Nomsa Dlamini', purpose:'Community development fund', family:'Dlamini Family', amount:450, due:'2026-10-31', status:'Overdue'},
    {id:'CT-1053', member:'Kagiso Mokoena', purpose:'Annual family contribution', family:'Mokoena Family', amount:650, due:'2026-11-30', status:'Pending'},
    {id:'CT-1054', member:'Bontle Molefe', purpose:'Event support', family:'Molefe Family', amount:300, due:'2026-12-15', status:'Pending'},
    {id:'CT-1055', member:'Ayanda Nkosi', purpose:'Community development fund', family:'Nkosi Family', amount:450, due:'2026-11-30', status:'Paid'}
  ],
  payments: [
    {id:'PAY-8021',member:'Thabo Mokoena',reference:'CT-1048',method:'EFT',date:'2026-11-09',amount:650,status:'Completed'},
    {id:'PAY-8020',member:'Naledi Mokoena',reference:'CT-1049',method:'Card',date:'2026-11-07',amount:650,status:'Completed'},
    {id:'PAY-8019',member:'Sibusiso Nkosi',reference:'CT-1051',method:'EFT',date:'2026-11-05',amount:650,status:'Completed'},
    {id:'PAY-8018',member:'Ayanda Nkosi',reference:'CT-1055',method:'Cash',date:'2026-11-03',amount:450,status:'Completed'},
    {id:'PAY-8017',member:'Lerato Molefe',reference:'CT-1012',method:'EFT',date:'2026-10-23',amount:450,status:'Completed'},
  ],
  meetings: [
    {id:'EV01',title:'Annual Family Gathering',type:'Gathering',date:'2026-12-12',time:'10:00',location:'Community Hall, Johannesburg',description:'A day to connect, celebrate our heritage and plan for the coming year.',attendees:85},
    {id:'EV02',title:'Leadership Committee Meeting',type:'Meeting',date:'2026-11-28',time:'14:00',location:'Online · Video conference',description:'Review family programmes, budget priorities and upcoming activities.',attendees:12},
    {id:'EV03',title:'Youth Development Workshop',type:'Workshop',date:'2026-12-05',time:'09:30',location:'Durban, KwaZulu-Natal',description:'Mentorship, careers and education opportunities for young members.',attendees:32},
  ],
  documents: [
    {id:'D001',name:'Family Constitution',category:'Governance',type:'PDF',size:'1.2 MB',updated:'2026-10-12',by:'Office of the Secretary'},
    {id:'D002',name:'2026 Annual Meeting Minutes',category:'Meetings',type:'PDF',size:'842 KB',updated:'2026-10-28',by:'Naledi Mokoena'},
    {id:'D003',name:'Contribution Guidelines',category:'Finance',type:'PDF',size:'506 KB',updated:'2026-09-08',by:'Finance Committee'},
    {id:'D004',name:'Family Branch Directory',category:'Membership',type:'DOCX',size:'1.8 MB',updated:'2026-11-01',by:'Office of the Secretary'},
    {id:'D005',name:'Youth Programme Plan',category:'Programmes',type:'PDF',size:'694 KB',updated:'2026-10-17',by:'Youth Coordinator'},
  ],
  activity: [
    {icon:'user-plus',color:'green',title:'Bontle Molefe requested to join',detail:'Membership · Northern Branch',time:'2 hours ago'},
    {icon:'credit-card',color:'amber',title:'Contribution received from Ayanda Nkosi',detail:'Finance · R 450.00',time:'Yesterday'},
    {icon:'calendar-days',color:'blue',title:'Annual Family Gathering announced',detail:'Events · 12 December 2026',time:'3 days ago'},
    {icon:'file-text',color:'purple',title:'Family Branch Directory updated',detail:'Documents · Membership',time:'4 days ago'}
  ]
};
