class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  async clickLinkAbout() {
    await this.page.click('text="About"');
  }

  async clickLinkStore() {
    await this.page.click('text="Store"');
  }

  async clickLinkGmail() {
    await this.page.click('[aria-label="Gmail "]');
  }

  async clickLinkImages() {
    await this.page.click('text="Images"');
  }

  async clickLinkSignIn() {
    await this.page.click('text="Sign in"');
  }

  async waitForDivShare() {
    await this.page.waitForSelector('[aria-label="Share"]');
  }

  async clickButtonSpchx() {
    await this.page.click('#spchx');
  }

  async fillTextareaSearch() {
    await this.page.fill('[name="q"]', '');
  }

  async waitForDivClear() {
    await this.page.waitForSelector('[aria-label="Clear"]');
  }

  async waitForDivFzj3ad() {
    await this.page.waitForSelector('.fzj3ad');
  }

  async waitForDivEtxtjc() {
    await this.page.waitForSelector('.etxtjc');
  }

  async waitForSpanJob8vb() {
    await this.page.waitForSelector('.Job8vb');
  }

  async waitForDivSeeMore() {
    await this.page.waitForSelector('[aria-label="See more"]');
  }

  async waitForDivClose() {
    await this.page.waitForSelector('[aria-label="Close"]');
  }

  async fillInputScaEsv() {
    await this.page.fill('[name="sca_esv"]', '');
  }

  async fillInputSource() {
    await this.page.fill('[name="source"]', '');
  }

  async fillInputEi() {
    await this.page.fill('[name="ei"]', '');
  }

  async fillInputIflsig() {
    await this.page.fill('[name="iflsig"]', '');
  }

  async clickLinkHindi() {
    await this.page.click('text="हिन्दी"');
  }

  async clickLinkBangla() {
    await this.page.click('text="বাংলা"');
  }

  async clickLinkTelugu() {
    await this.page.click('text="తెలుగు"');
  }

  async clickLinkMarathi() {
    await this.page.click('text="मराठी"');
  }

  async clickLinkTamil() {
    await this.page.click('text="தமிழ்"');
  }

  async clickLinkGujarati() {
    await this.page.click('text="ગુજરાતી"');
  }

  async clickLinkKannada() {
    await this.page.click('text="ಕನ್ನಡ"');
  }

  async clickLinkMalayalam() {
    await this.page.click('text="മലയാളം"');
  }

  async clickLinkPunjabi() {
    await this.page.click('text="ਪੰਜਾਬੀ"');
  }

  async clickLinkAdvertising() {
    await this.page.click('text="Advertising"');
  }

  async clickLinkBusiness() {
    await this.page.click('text="Business"');
  }

  async clickLinkHowSearchWorks() {
    await this.page.click('text="How Search works"');
  }

  async clickLinkPrivacy() {
    await this.page.click('text="Privacy"');
  }

  async clickLinkTerms() {
    await this.page.click('text="Terms"');
  }

  async clickDivSettings() {
    await this.page.click('text="Settings"');
  }

  async clickLinkSearchSettings() {
    await this.page.click('text="Search settings"');
  }

  async clickLinkAdvancedSearch() {
    await this.page.click('text="Advanced search"');
  }

  async clickLinkYourDataInSearch() {
    await this.page.click('text="Your data in Search"');
  }

  async clickLinkSearchHistory() {
    await this.page.click('text="Search history"');
  }

  async clickLinkSearchHelp() {
    await this.page.click('text="Search help"');
  }

  async waitForDivDarkThemeOff() {
    await this.page.waitForSelector('.tFYjZe');
  }

  async fillTextareaCsi() {
    await this.page.fill('[name="csi"]', '');
  }

  async waitForDivK1zIA() {
    await this.page.waitForSelector('.k1zIA');
  }

  async waitForDivFeedback() {
    await this.page.waitForSelector('.C85rO');
  }

  async waitForDivReportInappropriate() {
    await this.page.waitForSelector('.WzNHm');
  }
}