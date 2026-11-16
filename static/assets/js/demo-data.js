/** Illustrative local-only records shaped to mirror the existing Django models.
 *  No exported account data, payment credentials or personal identifiers are included. */
window.BAKGOMONG_SAMPLE = {
  accounts: [
    {id:'a1',username:'naledi',first_name:'Naledi',last_name:'Malla',title:'MS',gender:'FEMALE',maiden_name:'',email:'naledi@example.test',phone:'072 000 0001',address:'Gauteng, South Africa',family:'f1',role:'MEMBER',biography:'Member of Bakgomong Kgotla ya Malla.',id_number:'',birth_date:'1991-03-11',employment_status:'EMPLOYED',member_classification:'RELATIVE',langueges_spoken:'Setswana, English',is_approved:true,is_family_leader:false,created:'2026-01-20'},
    {id:'a2',username:'kabelo',first_name:'Kabelo',last_name:'Malla',title:'MR',gender:'MALE',maiden_name:'',email:'kabelo@example.test',phone:'072 000 0002',address:'Gauteng, South Africa',family:'f1',role:'KGOSANA',biography:'',id_number:'',birth_date:'1972-06-02',employment_status:'RETIRED',member_classification:'PARENT',langueges_spoken:'Setswana',is_approved:true,is_family_leader:true,created:'2026-01-17'},
    {id:'a3',username:'thato',first_name:'Thato',last_name:'Malla',title:'MR',gender:'MALE',maiden_name:'',email:'thato@example.test',phone:'072 000 0003',address:'North West, South Africa',family:'f2',role:'TREASURER',biography:'',id_number:'',birth_date:'1987-11-02',employment_status:'EMPLOYED',member_classification:'RELATIVE',langueges_spoken:'Setswana, English',is_approved:true,is_family_leader:false,created:'2026-02-01'},
    {id:'a4',username:'lerato',first_name:'Lerato',last_name:'Malla',title:'MRS',gender:'FEMALE',maiden_name:'',email:'lerato@example.test',phone:'072 000 0004',address:'North West, South Africa',family:'f2',role:'MEMBER',biography:'',id_number:'',birth_date:'1984-08-14',employment_status:'SELF_EMPLOYED',member_classification:'PARENT',langueges_spoken:'Setswana',is_approved:true,is_family_leader:true,created:'2026-02-01'},
    {id:'a5',username:'tumelo',first_name:'Tumelo',last_name:'Malla',title:'MR',gender:'MALE',maiden_name:'',email:'tumelo@example.test',phone:'072 000 0005',address:'Limpopo, South Africa',family:'f3',role:'SECRETARY',biography:'',id_number:'',birth_date:'1989-01-10',employment_status:'EMPLOYED',member_classification:'RELATIVE',langueges_spoken:'Sepedi, Setswana',is_approved:true,is_family_leader:true,created:'2026-02-06'},
    {id:'a6',username:'dineo',first_name:'Dineo',last_name:'Malla',title:'MS',gender:'FEMALE',maiden_name:'',email:'dineo@example.test',phone:'072 000 0006',address:'Limpopo, South Africa',family:'f3',role:'MEMBER',biography:'',id_number:'',birth_date:'2001-07-17',employment_status:'STUDENT',member_classification:'CHILD',langueges_spoken:'Setswana, English',is_approved:true,is_family_leader:false,created:'2026-03-05'},
    {id:'a7',username:'neil',first_name:'Neo',last_name:'Malla',title:'MR',gender:'MALE',maiden_name:'',email:'neo@example.test',phone:'072 000 0007',address:'Free State, South Africa',family:'f4',role:'MEMBER',biography:'',id_number:'',birth_date:'1996-05-21',employment_status:'EMPLOYED',member_classification:'RELATIVE',langueges_spoken:'Sesotho, English',is_approved:false,is_family_leader:true,created:'2026-04-12'},
    {id:'a8',username:'keabetswe',first_name:'Keabetswe',last_name:'Malla',title:'MRS',gender:'FEMALE',maiden_name:'',email:'keabetswe@example.test',phone:'072 000 0008',address:'Free State, South Africa',family:'f4',role:'MEMBER',biography:'',id_number:'',birth_date:'1993-04-12',employment_status:'EMPLOYED',member_classification:'RELATIVE',langueges_spoken:'Sesotho',is_approved:true,is_family_leader:false,created:'2026-04-22'}
  ],
  families: [
    {id:'f1',name:'Malla Main Family',slug:'malla-main-family',leader:'a2',is_approved:true,created:'2026-01-17'},
    {id:'f2',name:'Malla North West Family',slug:'malla-north-west-family',leader:'a4',is_approved:true,created:'2026-02-01'},
    {id:'f3',name:'Malla Limpopo Family',slug:'malla-limpopo-family',leader:'a5',is_approved:true,created:'2026-02-05'},
    {id:'f4',name:'Malla Free State Family',slug:'malla-free-state-family',leader:'a7',is_approved:false,created:'2026-04-09'}
  ],
  contributionTypes: [
    {id:'c1',name:'Monthly Kgotla Contribution',slug:'monthly-kgotla-contribution',description:'Monthly contribution supporting core Kgotla programmes and administration.',category:'savings',family:null,amount:150,recurrence:'monthly',scope:'clan',due_date:null,created_by:'a3',is_active:true,created:'2026-02-01'},
    {id:'c2',name:'Kgotla Funeral Support Fund',slug:'kgotla-funeral-support-fund',description:'Once-off clan contribution allocated for funeral and bereavement support.',category:'burial',family:null,amount:250,recurrence:'once_off',scope:'clan',due_date:'2026-12-18',created_by:'a3',is_active:true,created:'2026-09-15'},
    {id:'c3',name:'Family Leadership Levy',slug:'family-leadership-levy',description:'Annual leadership contribution for registered family leaders.',category:'other',family:null,amount:300,recurrence:'annual',scope:'family_leaders',due_date:'2026-12-01',created_by:'a3',is_active:true,created:'2026-10-01'},
    {id:'c4',name:'Main Family Education Fund',slug:'main-family-education-fund',description:'Education support fund restricted to the Malla Main Family.',category:'education',family:'f1',amount:200,recurrence:'once_off',scope:'family',due_date:'2026-11-27',created_by:'a3',is_active:true,created:'2026-10-10'},
    {id:'c5',name:'Kgotla Executive Planning',slug:'kgotla-executive-planning',description:'Annual meeting and programme-planning contribution for executive office holders.',category:'event',family:null,amount:125,recurrence:'once_off',scope:'executives',due_date:'2026-12-08',created_by:'a3',is_active:true,created:'2026-10-12'}
  ],
  memberContributions: [
    {id:'mc1',account:'a1',contribution_type:'c1',amount_due:150,due_date:'2026-11-30',reference:'MC-DEMO-001',is_paid:'NOT_PAID',created:'2026-11-01'},
    {id:'mc2',account:'a1',contribution_type:'c2',amount_due:250,due_date:'2026-12-18',reference:'MC-DEMO-002',is_paid:'NOT_PAID',created:'2026-09-15'},
    {id:'mc3',account:'a1',contribution_type:'c4',amount_due:200,due_date:'2026-11-27',reference:'MC-DEMO-003',is_paid:'PAID',created:'2026-10-10'},
    {id:'mc4',account:'a1',contribution_type:'c1',amount_due:150,due_date:'2026-10-31',reference:'MC-DEMO-004',is_paid:'PAID',created:'2026-10-01'},
    {id:'mc5',account:'a2',contribution_type:'c1',amount_due:150,due_date:'2026-11-30',reference:'MC-DEMO-005',is_paid:'PAID',created:'2026-11-01'},
    {id:'mc6',account:'a2',contribution_type:'c3',amount_due:300,due_date:'2026-12-01',reference:'MC-DEMO-006',is_paid:'NOT_PAID',created:'2026-10-01'},
    {id:'mc7',account:'a3',contribution_type:'c1',amount_due:150,due_date:'2026-11-30',reference:'MC-DEMO-007',is_paid:'PAID',created:'2026-11-01'},
    {id:'mc8',account:'a3',contribution_type:'c5',amount_due:125,due_date:'2026-12-08',reference:'MC-DEMO-008',is_paid:'NOT_PAID',created:'2026-10-12'},
    {id:'mc9',account:'a4',contribution_type:'c3',amount_due:300,due_date:'2026-12-01',reference:'MC-DEMO-009',is_paid:'PENDING',created:'2026-10-01'},
    {id:'mc10',account:'a4',contribution_type:'c1',amount_due:150,due_date:'2026-11-30',reference:'MC-DEMO-010',is_paid:'NOT_PAID',created:'2026-11-01'},
    {id:'mc11',account:'a5',contribution_type:'c1',amount_due:150,due_date:'2026-11-30',reference:'MC-DEMO-011',is_paid:'PAID',created:'2026-11-01'},
    {id:'mc12',account:'a5',contribution_type:'c3',amount_due:300,due_date:'2026-12-01',reference:'MC-DEMO-012',is_paid:'NOT_PAID',created:'2026-10-01'},
    {id:'mc13',account:'a6',contribution_type:'c1',amount_due:150,due_date:'2026-11-30',reference:'MC-DEMO-013',is_paid:'NOT_PAID',created:'2026-11-01'},
    {id:'mc14',account:'a7',contribution_type:'c1',amount_due:150,due_date:'2026-11-30',reference:'MC-DEMO-014',is_paid:'NOT_PAID',created:'2026-11-01'},
    {id:'mc15',account:'a8',contribution_type:'c2',amount_due:250,due_date:'2026-12-18',reference:'MC-DEMO-015',is_paid:'NOT_PAID',created:'2026-09-15'}
  ],
  payments: [
    {id:'p1',member_contribution:'mc3',account:'a1',amount:200,payment_method:'bank',payment_method_type:'EFT',reference:'TRX-DEMO-101',receipt:'RCT-DEMO-101',is_approved:'APPROVED',payment_date:'2026-11-07',recorded_by:'a3',payment_verified_by:'a3'},
    {id:'p2',member_contribution:'mc4',account:'a1',amount:150,payment_method:'mobile',payment_method_type:'Yoco',reference:'TRX-DEMO-102',receipt:'RCT-DEMO-102',is_approved:'APPROVED',payment_date:'2026-10-29',recorded_by:'a3',payment_verified_by:'a3'},
    {id:'p3',member_contribution:'mc5',account:'a2',amount:150,payment_method:'cash',payment_method_type:'Cash',reference:'TRX-DEMO-103',receipt:'RCT-DEMO-103',is_approved:'APPROVED',payment_date:'2026-11-06',recorded_by:'a3',payment_verified_by:'a3'},
    {id:'p4',member_contribution:'mc7',account:'a3',amount:150,payment_method:'bank',payment_method_type:'Bank deposit',reference:'TRX-DEMO-104',receipt:'RCT-DEMO-104',is_approved:'APPROVED',payment_date:'2026-11-06',recorded_by:'a3',payment_verified_by:'a3'},
    {id:'p5',member_contribution:'mc9',account:'a4',amount:300,payment_method:'bank',payment_method_type:'EFT',reference:'TRX-DEMO-105',receipt:null,is_approved:'PENDING',payment_date:'2026-11-12',recorded_by:null,payment_verified_by:null},
    {id:'p6',member_contribution:'mc11',account:'a5',amount:150,payment_method:'cash',payment_method_type:'Cash',reference:'TRX-DEMO-106',receipt:'RCT-DEMO-106',is_approved:'APPROVED',payment_date:'2026-11-02',recorded_by:'a3',payment_verified_by:'a3'}
  ],
  kgotlaBalance:{id:'b1',title:'Opening Kgotla Bank Balance',balance:24500,updated:'2026-11-01'},
  expenses:[
    {id:'e1',title:'Kgotla Meeting Venue',amount:1800,description:'Venue hire for the community leadership meeting.',added_by:'a3',incurred_date:'2026-10-29',recurring:'once_off',approved:true},
    {id:'e2',title:'Family Welfare Assistance',amount:650,description:'Support for a family welfare programme.',added_by:'a3',incurred_date:'2026-11-03',recurring:'once_off',approved:true},
    {id:'e3',title:'Meeting Stationery',amount:250,description:'Printing and stationery costs.',added_by:'a5',incurred_date:'2026-11-09',recurring:'once_off',approved:false}
  ],
  documents:[
    {id:'d1',title:'Bakgomong Constitution',category:'policy',description:'Approved governance and community principles.',visibility:'clan',family:null,uploaded_by:'a5',created:'2026-10-03',file:null},
    {id:'d2',title:'October Leadership Meeting Minutes',category:'minutes',description:'Minutes for the executive committee meeting.',visibility:'private',family:null,uploaded_by:'a5',created:'2026-10-30',file:null},
    {id:'d3',title:'Family Education Programme',category:'event',description:'Programme overview for the Main Family.',visibility:'family',family:'f1',uploaded_by:'a2',created:'2026-11-01',file:null},
    {id:'d4',title:'Contribution and Finance Policy',category:'report',description:'Payment, verification and finance procedures.',visibility:'clan',family:null,uploaded_by:'a3',created:'2026-11-07',file:null}
  ],
  meetings:[
    {id:'m1',title:'Kgotla Year-End Gathering',description:'Annual community gathering and family connection.',meeting_type:'in_person',meeting_venue:'Community Hall (venue to be confirmed)',meeting_link:null,audience:'clan',family:null,meeting_date:'2026-12-12T10:00',meeting_end_date:'2026-12-12T15:00',meeting_status:'scheduled',created_by:'a5'},
    {id:'m2',title:'Executive Finance Review',description:'Review contributions and Kgotla expenditure.',meeting_type:'online',meeting_venue:null,meeting_link:null,audience:'executives',family:null,meeting_date:'2026-11-25T14:00',meeting_end_date:'2026-11-25T15:30',meeting_status:'scheduled',created_by:'a5'},
    {id:'m3',title:'Family Leaders Planning Session',description:'Leadership priorities for next year.',meeting_type:'in_person',meeting_venue:'Kgotla office (demo venue)',meeting_link:null,audience:'family_leaders',family:null,meeting_date:'2026-12-05T11:00',meeting_end_date:'2026-12-05T13:00',meeting_status:'scheduled',created_by:'a5'}
  ]
};
