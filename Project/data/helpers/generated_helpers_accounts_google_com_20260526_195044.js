class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // element_id=0, tag=input, stable=true
  async fillInputGeneric(value) {
    await this.page.fill("#firstName", value);
  }

  // element_id=1, tag=input, stable=true
  async fillInputGeneric2(value) {
    await this.page.fill("[name=\"lastName\"]", value);
  }

  // element_id=2, tag=button, stable=true
  async clickButtonNext() {
    await this.page.click(".VfPpkd-LgbsSe");
  }

  // element_id=3, tag=a, stable=true
  async clickLinkHelp() {
    await this.page.click("text=\"Help\"");
  }

  // element_id=4, tag=a, stable=true
  async clickLinkPrivacy() {
    await this.page.click("text=\"Privacy\"");
  }

  // element_id=5, tag=a, stable=true
  async clickLinkTerms() {
    await this.page.click("text=\"Terms\"");
  }

  // element_id=6, tag=textarea, stable=true
  async fillTextareaGeneric(value) {
    await this.page.fill(".g-recaptcha-response", value);
  }

  // element_id=7, tag=h1, stable=true
  async waitForHeadingCreateA() {
    await this.page.waitForSelector("#headingText", { state: 'visible' });
  }

}

module.exports = GeneratedPageHelpers;