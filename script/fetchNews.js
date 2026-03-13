import axios from 'axios'
import fs from 'fs'
import { XMLParser } from 'fast-xml-parser'

const RSS = 'https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JXVnVMVlZUR2dKVlV5Z0FQAQ?hl=en-US&gl=US&ceid=US:en'

async function run() {
  const res = await axios.get(RSS, {
    headers: { 'User-Agent': 'Mozilla/5.0' },
  })

  const parser = new XMLParser()
  const json = parser.parse(res.data)

  const items = json.rss.channel.item.map((i) => ({
    title: i.title,
    link: i.link,
    pubDate: i.pubDate,
    source: i.source?.['#text'] || '',
    description: i.description,
  }))

  fs.writeFileSync('./data/news.json', JSON.stringify(items, null, 2))

  console.log('news updated:', items.length)
}

run()
