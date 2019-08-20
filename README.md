# hathitools
Tools for working with Hathi Trust Research Center extracted features files.

The HTRC extracted features files provide page-level word count data for ~15M volumes.
This package provides some simple tools for extracting information from these files about word usage.
These scripts are tested on a Mac and should work on linux, but will probably cause problems on Windows except through the bash subsystem.

To start, create a set of selected volume IDs from Hathi Trust.
One good option is the [Workset Builder 2.0](https://solr2.htrc.illinois.edu/solr-ef) search interface.
Construct a search, and then download "Volume Metadata" in JSON format.
As an example, I searched for volumes whose metadata contains `mexican war`.
The page will save as `htrc-metadata-export.json`.
The download may take a while, depending on the number of selected volumes.
Here is an example record from this file:

    {"htBibUrl":"http://catalog.hathitrust.org/api/volumes/full/htid/aeu.ark:/13960/t44q9g792.json","lastUpdateDate":"2014-09-18 03:45:48","isbn":["0665834071"],"imprint":"Yale University Press; Glasgow, Brook, 1921.","accessProfile":"open","language":"eng","typeOfResource":"text","title":"Texas and the Mexican War a chronicle of the winning of the Southwest / by Nathaniel W. Stephenson.","lccn":[],"dateCreated":"2016-06-19T07:39:10.5311367Z","enumerationChronology":" ","genre":["not fiction"],"pubPlace":"ctu","hathitrustRecordNumber":"100300175","schemaVersion":"1.3","sourceInstitutionRecordNumber":"","volumeIdentifier":"aeu.ark:/13960/t44q9g792","rightsAttributes":"pdus","classification":{"ddc":["976.4/04"]},"pubDate":"1921","governmentDocument":false,"sourceInstitution":"AEU","bibliographicFormat":"BK","names":["Stephenson, Nathaniel W. (Nathaniel Wright) 1867-1935 "],"issn":[],"handleUrl":"http://hdl.handle.net/2027/aeu.ark:/13960/t44q9g792","oclc":["564591684"],"issuance":"monographic"}

The script `bin/json2ids.py` reads this file and outputs a new file containing paths suitable for `rsync`.
It's based on examples from [this HTRC notebook](https://github.com/htrc/htrc-feature-reader/blob/master/examples/ID_to_Rsync_Link.ipynb).

    python bin/json2ids.py ~/Downloads/htrc-metadata-export.json > mexican_war_agenda.txt

The resulting file contains one line per volume. IDs are expanded to full paths using the "pairtree" method.

    aeu/pairtree_root/ar/k+/=1/39/60/=t/44/q9/g7/92/ark+=13960=t44q9g792/aeu.ark+=13960=t44q9g792.json.bz2
    aeu/pairtree_root/ar/k+/=1/39/60/=t/58/d0/rk/2g/ark+=13960=t58d0rk2g/aeu.ark+=13960=t58d0rk2g.json.bz2
    ...

I then download the extracted features files to a new directory.

    mkdir mexican_war
    rsync -av --no-relative --files-from mexican_war_agenda.txt data.analytics.hathitrust.org::features/ mexican_war

The files in this directory correspond to volumes in the workset.
Each file is a JSON file compressed using the `bzip2` method.

The next step is to convert the `.json.bz2` features files into something more readable.
My preferred file format is a three column tab-delimited file (this is the default for Mallet).
Since we do not have words in order in the extracted features file, it is difficult to get any useful information from high-frequency words like determiners, conjunctions, and prepositions.
I created a minimal stoplist in the file `stoplist.txt`, containing words that I will not record.
I am also dropping information about word frequency within pages, and only record that a word was present at least once.
For pages this is not a terrible approximation.

    python bin/bz_to_text.py mexican_war stoplist.txt > mexican_war.txt

Here's an example of the result:

    hvd.32044021238100	X	federals killed second defeated john success his too among force judging hill soon struck than march three himself breaking hasten engagement advancing what line troops captured fell must him battle opportune advanced wished came blow capturing before afterwards intended howard two  height accomplished reinforcements forward daylight early coming commanding troopers men then these overwhelmed they far resulted prisoners until division army wounded upon decisive now did gained driven colors dispositions just concentrated found through been pressing ewell also general being day—lee after engaged third sickles cemetery brigadier-generals longstreet back their moment heth routed pender reynolds formed brigades retreated exclusive fight divisions could bring archer federal sent general confederates gettysburg whole its cannon mainly two attack where get lee loss were several more union begun confederate joined rodes lines against word made moved when pushed possible one meade wish corps brilliant

I'm removing punctuation and all other non-Unicode-letter characters from the ends of words, but not from the middle. I'm also not removing ligatures, so fi and fl ligature characters may still be present.
The first field is the volume ID, which originated from Harvard libraries.
The `X` in the second field is a placeholder, since Mallet by default assumes there will be three columns in input files.

This file is fine for use with Mallet, but for matrix operations I have a slightly more compact format that represents word IDs as base 64 strings.
Base 64 is a binary format that represents numbers as printable letter characters.
To encode this file we first need to construct a vocabulary, which I limit to 65536 (ie 2<sup>16</sup>) entries.
This is large enough for most purposes but fits in two bytes, so we can print it in base 64 without a lot of wasted bits.

    python bin/text_vocab.py mexican_war.txt > vocab64.mexican_war

Words in this file are arranged in descending order by frequency. The top words are *his*, *were*, *they*, which are the most common words not appearing in my minimal stoplist.
Given this vocabulary mapping strings to numbers, I can now produce a compressed representation of the page token information.

    python bin/tokens_to_base64.py vocab64.mexican_war mexican_war.txt b64.mexican_war

The resulting output for the page we previously displayed is:

    hvd.32044021238100	X	HBHVB98LAw2mAdgAWAFaH+QBAQCQEQsAAwBQArECewAbBzUF8g0qAg8NoACOAW8D/B+rA98IUgD8DhwCDgGRAesBOwFrCA4AIwSHASQpoACoAikNvwCcBQAACwkDAIIDuwB/FLcCZwFeDhkBAwTwEycAEQCZAGbsCAhrBGEEJgBdAEgAiwP1AqsEdDS1ASEVIBGMAHo9QwAIABQEPQAHAIgUQd4xAEEAfgMDAUQBfQJNCFsAxAHhD2pSigk+E9ICRgChAKkBBQBwNN0JNQfwAWUD7QCnAQcAXgSXCnoA0RZPGWECEgASApMAywNOA64F5QBLAMsAbgBvAc0EAABZBkkBZAf9ACwA6AGLZRcEtw99ANcIMwCPCdwA1gV/BIw24AGQAI0GBgWLAQ==

The script `bin/multiply.py` produces a vector representation of each word in the vocabulary.
Technically this is an approximate eigenvector decomposition using 10 iterations of the iterated subspace algorithm.
It's equivalent to Latent Semantic Analysis (LSA).

    python bin/multiply.py b64.mexican_war vocab64.mexican_war

The streaming matrix multiply is fairly efficient, but takes a while. For the 500-volume Mexican War collection it is done in about five minutes.
This script produces a file called `embeddings.txt`:

    his -0.17046289710428236 -0.048829368247665955 -0.00011366652487146231 -0.003885293511609003 -0.03100028748949623 -0.015697542606138114 0.0029981629387524677 -0.23378770551397143 -0.19732011191668974 0.021442434080682114...

This has one line for each word in the vocabulary, with a 100-dimensional representation of the word in vector space.
A convenient way to explore this vector space is to find k-means clusters.

    python bin/kmeans.py embeddings.txt 100

The resulting clusters are pretty coherent, to me. Words are presented in descending order by corpus frequency. Here are seven randomly selected ones:

Describing the position and movement of armies, combat engineers

> way position road advance front strong division rear brigade hill cut generals leading turn twiggs village mile follow flank engineers supported pillow divisions positions churubusco fortified duncan reserve shields pierce engineer contreras turning brigades riley closely grounds angel harney causeway sumner tower reconnoissance beauregard valencia courier intrenchments impracticable reconnaissance canal convent augustine chalco stormed fortification sweep crest southeast flanked reverse diversion highway flanking pont augustin assaulted cadwallader guided intrenched acapulco hamlet reconnoitering penon pablo slopes composing divert tete lava reconnoiter antonia mask reconnoitring persifor blocked padierna ayotla shaken precipitated mexicalcingo assail marshes pedregal field-work coyoacan rincon xochimilco reconnoitered agustin toluca

Letters home? (Read with sad Ken Burns fiddle tune)

> has soon few here days last can must nothing leave get hope better find enough think doubt news things gone fear hear feel doing yesterday health to-day chance learn safe dear stop expect write genl pleased truly start mail to-morrow glad doctor rumors inst sorry bid thinks tomorrow presume rumor wishing sincerely intend apprehensions bless conceive pray enjoying finish spend affectionate dearest indulge ult annoyance uneasy disgusted good-night uneasiness informs comfortably govt dined omit mentioning compy mails heavenly laidley infy remembering belton thankful tampa chill intends individually recd indisposed chat betty worry cheaper doings chills bye qrs i8th majr httle

Poetic language about war

> death heart blood alone words longer presence love save earth voice fair live happy die lie cast scenes grave hearts heaven silent sad soul forgotten mercy mighty sweet spoken alive forever fears pain tears victims forget thoughts pure loved beside bosom ear wives repose adventure passion soft gather victim melancholy vision brow gentle imagination perished delight song souls dread prayer breath touch misery cabin circle sorrow prey lovely tongue sleeping thou dream toil eternal grief fancy grasp stirring trace deed agony sisters infant tie behold shadow thy kindred lights tale parting burial endure helpless blessed flower memories desolation sublime gaze

Descriptions of urban environments

> city large church houses principal appearance beautiful streets street building square buildings plaza cities entrance silver picture corner churches cathedral floor garden roof windows handsome presenting taste flowers shut marks doors bells finest gardens curiosity orange rooms altar lined furniture dwellings feast fountain brick virgin neat shops suburbs wrought sorts outskirts marble temples ornaments elaborate regularity displaying richly silk gambling adorned feathers locked paved ornamented statue forbidding paintings walks architecture altars superb carved females spacious pulque candles italian sexes profusion blocks balconies saviour oranges amusements bricks apartments bernal dresses dome palaces neatly wines gaudy gilded edifices floors fountains pavement jewels

Ships and sea travel

> off land island navy vessels board squadron ship commodore sea coast naval ships armed port fleet shore carrying vessel boats landed bay landing gulf lying sailed sail boat harbor perry ports frigate steamer sailors strike loaded admiral destined marine conner blockade embarked bar anchor safely transports smaller seamen islands ashore schooner harbour cruise voyage accident merchant repair sloop breeze shores anchored decatur transport cape channel sunk yard manned steamers frigates pulled shipping chesapeake armament eastward fitted aboard schooners crews alvarado indies transfer steam blown gale seas blowing sailor newport gunboats flotilla cargo anchorage blew convoy craft dale gun-boats coasts junior

Adverbs

> some very little good small old quite fine bad sometimes frequently somewhat hot perfectly pretty sort mostly occasionally ones exceedingly finished dress hair dressed eat mixed plenty color drink kinds sit glass wear couple pair buy fish tobacco delighted wine drinking thin wooden skin huts clean holes dirty remarkably drank fat hats sport shirt nice straw vegetables amused beans amusement cards dried stick humor coats polite smallest lucky tolerably merry tight bottle grows keeps creatures fare turkey boots complexion coarse trunk pipe milk cow fandango chickens clever linen pleasantly eggs mixture packing earthen bottles bathing boiled potatoes cleaning sticks sack

Traveling in desert environments

> miles reached along distance water pass horses mountains route distant passing wagons marching encamped stream hills reaching halted fields journey animals plains rain rough corn wagon prairie cattle encountered grass desert bed rocks halt dry trail fires path sierra snow companions extremely marches travel bottom streams signs timber rancho scouts brush rugged mud sandy traveled track impassable ice sunrise thirst sheep barren camped naked scenery pace ascending rains grain deer pitched prairies delightful traversed rainy oxen beasts guides halting arid peak dreaded monclova hunters vegetation thickets feed straggling crosses travelling travelled beds frozen precipitous deserts adobe desolate peaks cactus wolves
