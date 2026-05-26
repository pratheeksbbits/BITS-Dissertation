class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // Interact with the Wikipedia logo
  async clickWikipediaLogo() {
    await this.page.click('.central-textlogo-wrapper');
  }

  // Assert visibility of "The Free Encyclopedia" text
  async assertTheFreeEncyclopediaVisible() {
    await this.page.waitForSelector('text="The Free Encyclopedia"', { state: 'visible' });
  }

  // Interact with the "Search Wikipedia" label
  async assertSearchWikipediaVisible() {
    await this.page.waitForSelector('text="Search Wikipedia"', { state: 'visible' });
  }

  // Interact with the language label (EN)
  async assertLanguageLabelVisible() {
    await this.page.waitForSelector('#jsLangLabel', { state: 'visible' });
  }

  // Assert visibility of "We owe you an explanation." text
  async assertExplanationHeaderVisible() {
    await this.page.waitForSelector('h3', { state: 'visible' });
  }

  // Interact with the "Download Wikipedia for Android or iOS" text
  async clickDownloadWikipedia() {
    await this.page.click('text="Download Wikipedia for Android or iOS"');
  }
}

module.exports = GeneratedPageHelpers;