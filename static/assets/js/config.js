/** Frontend-only settings to be replaced by server-side Django configuration.
 * Never put bank credentials or Yoco secret keys in this file.
 * Bank instructions should be supplied by an authorised Kgotla administrator.
 */
window.BAKGOMONG_CONFIG = {
  bankName: 'To be supplied by Kgotla management',
  accountName: 'To be supplied by Kgotla management',
  accountNumber: 'Not configured — verify with the Treasurer',
  branchCode: 'Not configured',
  proofEmail: 'Not configured — ask the Secretary / Treasurer',
  managerContact: 'Your family leader or Kgotla Secretary / Administrator',
  yocoCheckoutUrl: '' // Must be a backend-generated, per-checkout hosted URL. Never hardcode a merchant key.
};
