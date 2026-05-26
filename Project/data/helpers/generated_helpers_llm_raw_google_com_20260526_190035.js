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
    await this.page.click('text="Gmail"');
  }

  async clickLinkImages() {
    await this.page.click('text="Images"');
  }

  async clickLinkSignIn() {
    await this.page.click('text="Sign in"');
  }

  async clickButtonSpeechRecognition() {
    await this.page.click('#spchx');
  }

  async fillTextareaSearchQuery(value) {
    await this.page.fill('[name="q"]', value);
  }

  async clickButtonClearSearch() {
    await this.page.click('[aria-label="Clear"]');
  }

  async clickDivReportInappropriatePredictions() {
    await this.page.click('.WzNHm');
  }

  async clickButtonClose() {
    await this.page.click('[aria-label="Close"]');
  }

  async fillInputScaEsv(value) {
    await this.page.fill('[name="sca_esv"]', value);
  }

  async fillInputSource(value) {
    await this.page.fill('[name="source"]', value);
  }

  async fillInputEi(value) {
    await this.page.fill('[name="ei"]', value);
  }

  async fillInputIflsig(value) {
    await this.page.fill('[name="iflsig"]', value);
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

  async clickDivDarkThemeToggle() {
    await this.page.click('.tFYjZe');
  }

  async fillTextareaCsi(value) {
    await this.page.fill('[name="csi"]', value);
  }

  async clickSpanClose() {
    await this.page.click('[aria-label="Close"]');
  }

  async clickDivFeedbackOptions() {
    await this.page.click('.C85rO');
  }

  async clickDivFeedbackContainer() {
    await this.page.click('.Wm2B8c');
  }
}

module.exports = GeneratedPageHelpers;