# anki-backfill-scripts

Currently contains `backfill_context.py`, a simple script to search for sentences within your source and add the surrounding sentences to your Anki card.

# TODO
- (done) Search sentences better! A better way of searching sentences would be:
    - Remove whitespace from string
    - Concatenate all lines into one string
    - Search for substring in processed string
    - Use a structure to map the begin/end index of the processed string back to the array of lines
        - i.e. an array with each row being: og_sentence, modified_sentence, length of all modified_sentences before this row
- Support epub better: Integrate calibre
- Support subtitle files
    - https://github.com/fedecalendino/pysub-parser
    - https://github.com/tkarabela/pysubs2
    - etc?
- Support list of files (i.e. to backfill an entire season of subtitle files)

# Also See
- [DillonWall/generate-batch-audio-anki-addon](https://github.com/DillonWall/generate-batch-audio-anki-addon): Can backfill audio using a [local audio server](https://github.com/themoeway/local-audio-yomichan)
- [AJT Japanese](https://ankiweb.net/shared/info/1344485230): Backfill furigana/readings, pitch accent info, and audio.
- [MarvNC/JP-Resources](https://github.com/MarvNC/JP-Resources): Backfill frequencies
- [FieldReporter](https://ankiweb.net/shared/info/569864517): Backfill frequencies
