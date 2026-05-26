class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  async fillInputFirstName(value) {
    await this.page.fill('#firstName', value);
  }

  async fillInputLastName(value) {
    await this.page.fill('[name="lastName"]', value);
  }

  async clickButtonNext() {
    await this.page.click('.VfPpkd-LgbsSe');
  }

  async clickLinkHelp() {
    await this.page.click('text="Help"');
  }

  async clickLinkPrivacy() {
    await this.page.click('text="Privacy"');
  }

  async clickLinkTerms() {
    await this.page.click('text="Terms"');
  }

  async fillTextareaGeneric(value) {
    await this.page.fill('.g-recaptcha-response', value);
  }

  async waitForHeadingCreateGoogleAccount() {
    await this.page.waitForSelector('#headingText');
  }
}

export default GeneratedPageHelpers;