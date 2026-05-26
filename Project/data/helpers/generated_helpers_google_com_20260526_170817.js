class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  async clickAbout() {
    await this.page.click('text="About"');
  }

  async clickStore() {
    await this.page.click('text="Store"');
  }

  async clickGmail() {
    await this.page.click('text="Gmail"');
  }

  async clickImages() {
    await this.page.click('text="Images"');
  }

  async clickSignIn() {
    await this.page.click('text="Sign in"');
  }

  async clickGoogleApps() {
    await this.page.click('.gb_C');
  }

  async fillSearchInput(value) {
    await this.page.fill('[name="q"]', value);
  }

  async clickClearSearch() {
    await this.page.click('[aria-label="Clear"]');
  }

  async clickReportInappropriatePredictions() {
    await this.page.click('.WzNHm');
  }

  async clickClose() {
    await this.page.click('[aria-label="Close"]');
  }

  async fillScaEsv(value) {
    await this.page.fill('[name="sca_esv"]', value);
  }

  async fillSource(value) {
    await this.page.fill('[name="source"]', value);
  }

  async fillEi(value) {
    await this.page.fill('[name="ei"]', value);
  }

  async fillIflsig(value) {
    await this.page.fill('[name="iflsig"]', value);
  }

  async clickHindi() {
    await this.page.click('text="हिन्दी"');
  }

  async clickBangla() {
    await this.page.click('text="বাংলা"');
  }

  async clickTelugu() {
    await this.page.click('text="తెలుగు"');
  }

  async clickMarathi() {
    await this.page.click('text="मराठी"');
  }

  async clickTamil() {
    await this.page.click('text="தமிழ்"');
  }

  async clickGujarati() {
    await this.page.click('text="ગુજરાતી"');
  }

  async clickKannada() {
    await this.page.click('text="ಕನ್ನಡ"');
  }

  async clickMalayalam() {
    await this.page.click('text="മലയാളം"');
  }

  async clickPunjabi() {
    await this.page.click('text="ਪੰਜਾਬੀ"');
  }

  async clickAdvertising() {
    await this.page.click('text="Advertising"');
  }

  async clickBusiness() {
    await this.page.click('text="Business"');
  }

  async clickHowSearchWorks() {
    await this.page.click('text="How Search works"');
  }

  async clickPrivacy() {
    await this.page.click('text="Privacy"');
  }

  async clickTerms() {
    await this.page.click('text="Terms"');
  }

  async clickSettings() {
    await this.page.click('text="Settings"');
  }

  async clickSearchSettings() {
    await this.page.click('text="Search settings"');
  }

  async clickAdvancedSearch() {
    await this.page.click('text="Advanced search"');
  }

  async clickYourDataInSearch() {
    await this.page.click('text="Your data in Search"');
  }

  async clickSearchHistory() {
    await this.page.click('text="Search history"');
  }

  async clickSearchHelp() {
    await this.page.click('text="Search help"');
  }

  async clickDarkThemeToggle() {
    await this.page.click('.tFYjZe');
  }

  async fillCsi(value) {
    await this.page.fill('[name="csi"]', value);
  }

  async clickFeedbackOption() {
    await this.page.click('.C85rO');
  }

  async clickSeeMore() {
    await this.page.click('[aria-label="See more"]');
  }

  async clickElementFzj3ad() {
    await this.page.click('.fzj3ad');
  }

  async clickElementEtxtjc() {
    await this.page.click('.etxtjc');
  }

  async clickElementJob8vb() {
    await this.page.click('.Job8vb');
  }

  async clickElementK1zIA() {
    await this.page.click('.k1zIA');
  }
}

module.exports = GeneratedPageHelpers;