class GeneratedPageHelpers {
  constructor(page) {
    this.page = page;
  }

  // Click on the Wikipedia logo
  async clickWikipediaLogo() {
    await this.page.click('.central-textlogo-wrapper');
  }

  // Assert visibility of "The Free Encyclopedia" text
  async assertTheFreeEncyclopediaVisible() {
    await this.page.waitForSelector('text="The Free Encyclopedia"', { state: 'visible' });
  }

  // Assert visibility of "Search Wikipedia" label
  async assertSearchWikipediaLabelVisible() {
    await this.page.waitForSelector('text="Search Wikipedia"', { state: 'visible' });
  }

  // Assert visibility of language label "EN"
  async assertLanguageLabelENVisible() {
    await this.page.waitForSelector('#jsLangLabel', { state: 'visible' });
  }

  // Assert visibility of "We owe you an explanation." header
  async assertWeOweYouAnExplanationVisible() {
    await this.page.waitForSelector('h3', { state: 'visible' });
  }

  // Click on "Download Wikipedia for Android or iOS" link
  async clickDownloadWikipediaLink() {
    await this.page.click('text="Download Wikipedia for Android or iOS"');
  }
}

module.exports = GeneratedPageHelpers;