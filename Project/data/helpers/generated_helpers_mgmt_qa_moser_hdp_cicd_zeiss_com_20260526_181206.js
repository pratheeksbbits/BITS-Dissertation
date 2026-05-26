class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // Click on the "Admin Center" link
  async clickAdminCenter() {
    await this.page.click('.brand-text');
  }

  // Click on the customer button
  async clickCustomerButton() {
    await this.page.click('#btn-customer');
  }

  // Click on the user button
  async clickUserButton() {
    await this.page.click('#btn-user');
  }

  // Click on the text-only button
  async clickTextOnlyButton() {
    await this.page.click('.text-only');
  }

  // Assert visibility of the "Connectivity Module Provisioning" header
  async assertConnectivityModuleProvisioningHeaderVisible() {
    await this.page.waitForSelector('#cm-provisioning-txt-header', { state: 'visible' });
  }
}

module.exports = GeneratedPageHelpers;