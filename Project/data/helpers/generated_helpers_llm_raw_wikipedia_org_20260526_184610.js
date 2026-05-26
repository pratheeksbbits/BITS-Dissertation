class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // Click on the Wikipedia logo
  async clickHeadingWikipediaTheFreeEncyclopedia() {
    await this.page.click('.central-textlogo-wrapper');
  }

  // Assert visibility of "The Free Encyclopedia" text
  async waitForStrongTheFreeEncyclopedia() {
    await this.page.waitForSelector('text="The Free Encyclopedia"');
  }

  // Click on "English" language option
  async clickStrongEnglish() {
    await this.page.click('text="English"');
  }

  // Click on "日本語" language option
  async clickStrong日本語() {
    await this.page.click('/html/body/main/nav/div[2]/a/strong');
  }

  // Click on "Deutsch" language option
  async clickStrongDeutsch() {
    await this.page.click('/html/body/main/nav/div[3]/a/strong');
  }

  // Click on "Français" language option
  async clickStrongFrançais() {
    await this.page.click('/html/body/main/nav/div[4]/a/strong');
  }

  // Click on "Русский" language option
  async clickStrongРусский() {
    await this.page.click('/html/body/main/nav/div[5]/a/strong');
  }

  // Click on "中文" language option
  async clickStrong中文() {
    await this.page.click('/html/body/main/nav/div[6]/a/strong');
  }

  // Click on "Español" language option
  async clickStrongEspañol() {
    await this.page.click('/html/body/main/nav/div[7]/a/strong');
  }

  // Click on "Italiano" language option
  async clickStrongItaliano() {
    await this.page.click('/html/body/main/nav/div[8]/a/strong');
  }

  // Click on "Polski" language option
  async clickStrongPolski() {
    await this.page.click('/html/body/main/nav/div[9]/a/strong');
  }

  // Click on "Português" language option
  async clickStrongPortuguês() {
    await this.page.click('/html/body/main/nav/div[10]/a/strong');
  }

  // Assert visibility of "Search Wikipedia" label
  async waitForLabelSearchWikipedia() {
    await this.page.waitForSelector('text="Search Wikipedia"');
  }

  // Assert visibility of "EN" language label
  async waitForLabelEN() {
    await this.page.waitForSelector('#jsLangLabel');
  }

  // Assert visibility of "We owe you an explanation." heading
  async waitForHeadingWeOweYouAnExplanation() {
    await this.page.waitForSelector('h3');
  }

  // Assert visibility of "Download Wikipedia for Android or iOS" text
  async waitForStrongDownloadWikipediaForAndroidOrIOS() {
    await this.page.waitForSelector('text="Download Wikipedia for Android or iOS"');
  }
}

module.exports = GeneratedPageHelpers;