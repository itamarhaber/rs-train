# FT.AGGREGATE
## Syntax
```
query [VERBATIM] [LOAD count field [field ...]] [TIMEOUT timeout] [LOAD *] [GROUPBY nargs property [property ...] [REDUCE function nargs arg [arg ...] [AS name] [REDUCE function nargs arg [arg ...] [AS name] ...]] [GROUPBY nargs property [property ...] [REDUCE function nargs arg [arg ...] [AS name] [REDUCE function nargs arg [arg ...] [AS name] ...]] ...]] [SORTBY nargs [property <ASC | DESC> [property <ASC | DESC> ...]] [MAX num]] [APPLY expression AS name [APPLY expression AS name ...]] [LIMIT offset num] [FILTER filter] [WITHCURSOR [COUNT read_size] [MAXIDLE idle_time]] [PARAMS nargs name value [name value ...]] [DIALECT dialect]```

Run a search query on an index, and perform aggregate transformations on the results, extracting statistics etc from them

[Examples](#examples)

## Required arguments

<details open>
<summary><code>index</code></summary>

is index name against which the query is executed. You must first create the index using [`FT.CREATE`](/commands/ft.create).
</details>

<details open>
<summary><code>query</code></summary> 

is base filtering query that retrieves the documents. It follows the exact same syntax as the search query, including filters, unions, not, optional, and so on.
</details>

## Optional arguments

<details open>
<summary><code>VERBATIM</code></summary>

if set, does not try to use stemming for query expansion but searches the query terms verbatim.
</details>

<details open>
<summary><code>LOAD {nargs} {identifier} AS {property} …</code></summary> 

loads document attributes from the source document. 
 - `identifier` is either an attribute name for hashes and JSON or a JSON Path expression for JSON. 
 - `property` is the optional name used in the result. If it is not provided, the `identifier` is used. This should be avoided.
 - If `*` is used as `nargs`, all attributes in a document are loaded.

Attributes needed for aggregations should be stored as `SORTABLE`, where they are available to the aggregation pipeline with very low latency. `LOAD` hurts the performance of aggregate queries considerably because every processed record needs to execute the equivalent of [`HMGET`](/commands/hmget) against a Redis key, which when executed over millions of keys, amounts to high processing times.

<details open>
<summary><code>GROUPBY {nargs} {property}</code></summary> 

groups the results in the pipeline based on one or more properties. Each group should have at least one _reducer_, a function that handles the group entries,
  either counting them, or performing multiple aggregate operations (see below).
      
<details open>
<summary><code>REDUCE {func} {nargs} {arg} … [AS {name}]</code></summary>

reduces the matching results in each group into a single record, using a reduction function. For example, `COUNT` counts the number of records in the group. The reducers can have their own property names using the `AS {name}` optional argument. If a name is not given, the resulting name will be the name of the reduce function and the group properties. For example, if a name is not given to `COUNT_DISTINCT` by property `@foo`, the resulting name will be `count_distinct(@foo)`.
  
See [Supported GROUPBY reducers](/docs/interact/search-and-query/search/aggregations/#supported-groupby-reducers) for more details.   
</details>

<details open>
<summary><code>SORTBY {nargs} {property} {ASC|DESC} [MAX {num}]</code></summary> 

sorts the pipeline up until the point of `SORTBY`, using a list of properties. 

 - By default, sorting is ascending, but `ASC` or `DESC ` can be added for each property. 
 - `nargs` is the number of sorting parameters, including `ASC` and `DESC`, for example, `SORTBY 4 @foo ASC @bar DESC`.
 - `MAX` is used to optimized sorting, by sorting only for the n-largest elements. Although it is not connected to `LIMIT`, you usually need just `SORTBY … MAX` for common queries.

Attributes needed for `SORTBY` should be stored as `SORTABLE` to be available with very low latency.

**Sorting Optimizations**: performance is optimized for sorting operations on `DIALECT 4` in different scenarios:
   - Skip Sorter - applied when there is no sort of any kind. The query can return after it reaches the `LIMIT` requested results.
   - Partial Range - applied when there is a `SORTBY` clause over a numeric field, with no filter or filter by the same numeric field, the query iterate on a range large enough to satisfy the `LIMIT` requested results.
   - Hybrid - applied when there is a `SORTBY` clause over a numeric field and another non-numeric filter. Some results will get filtered, and the initial range may not be large enough. The iterator is then rewinding with the following ranges, and an additional iteration takes place to collect the `LIMIT` requested results.
   - No optimization - If there is a sort by score or by non-numeric field, there is no other option but to retrieve all results and compare their values.

**Counts behavior**: optional `WITHCOUNT` argument returns accurate counts for the query results with sorting. This operation processes all results in order to get an accurate count, being less performant than the optimized option (default behavior on `DIALECT 4`)


<details open>
<summary><code>APPLY {expr} AS {name}</code></summary> 

applies a 1-to-1 transformation on one or more properties and either stores the result as a new property down the pipeline or replaces any property using this
  transformation. 
  
`expr` is an expression that can be used to perform arithmetic operations on numeric properties, or functions that can be applied on properties depending on their types (see below), or any combination thereof. For example, `APPLY "sqrt(@foo)/log(@bar) + 5" AS baz` evaluates this expression dynamically for each record in the pipeline and store the result as a new property called `baz`, which can be referenced by further `APPLY`/`SORTBY`/`GROUPBY`/`REDUCE` operations down the
  pipeline.
</details>

<details open>
<summary><code>LIMIT {offset} {num}</code></summary> 

limits the number of results to return just `num` results starting at index `offset` (zero-based). It is much more efficient to use `SORTBY … MAX` if you
  are interested in just limiting the output of a sort operation.
  If a key expires during the query, an attempt to `load` the key's value will return a null array. 

However, limit can be used to limit results without sorting, or for paging the n-largest results as determined by `SORTBY MAX`. For example, getting results 50-100 of the top 100 results is most efficiently expressed as `SORTBY 1 @foo MAX 100 LIMIT 50 50`. Removing the `MAX` from `SORTBY` results in the pipeline sorting _all_ the records and then paging over results 50-100.
</details>

<details open>
<summary><code>FILTER {expr}</code></summary> 

filters the results using predicate expressions relating to values in each result.
  They are applied post query and relate to the current state of the pipeline.
</details>

<details open>
<summary><code>WITHCURSOR {COUNT} {read_size} [MAXIDLE {idle_time}]</code></summary> 

Scan part of the results with a quicker alternative than `LIMIT`.
See [Cursor API](/docs/interact/search-and-query/search/aggregations/#cursor-api) for more details.
</details>

<details open>
<summary><code>TIMEOUT {milliseconds}</code></summary> 

if set, overrides the timeout parameter of the module.
</details>

<details open>
<summary><code>PARAMS {nargs} {name} {value}</code></summary> 

defines one or more value parameters. Each parameter has a name and a value. 

You can reference parameters in the `query` by a `$`, followed by the parameter name, for example, `$user`. Each such reference in the search query to a parameter name is substituted by the corresponding parameter value. For example, with parameter definition `PARAMS 4 lon 29.69465 lat 34.95126`, the expression `@loc:[$lon $lat 10 km]` is evaluated to `@loc:[29.69465 34.95126 10 km]`. You cannot reference parameters in the query string where concrete values are not allowed, such as in field names, for example, `@loc`. To use `PARAMS`, set `DIALECT` to `2` or greater than `2`.
</details>

<details open>
<summary><code>DIALECT {dialect_version}</code></summary> 

selects the dialect version under which to execute the query. If not specified, the query will execute under the default dialect version set during module initial loading or via [`FT.CONFIG SET`](/commands/ft.config-set) command.
</details>

## Return

FT.AGGREGATE returns an array reply where each row is an array reply and represents a single aggregate result.
The [integer reply](/docs/reference/protocol-spec/#resp-integers) at position `1` does not represent a valid value.

### Return multiple values

See [Return multiple values](/commands/ft.search#return-multiple-values) in [`FT.SEARCH`](/commands/ft.search)
The `DIALECT` can be specified as a parameter in the FT.AGGREGATE command. If it is not specified, the `DEFAULT_DIALECT` is used, which can be set using [`FT.CONFIG SET`](/commands/ft.config-set) or by passing it as an argument to the `redisearch` module when it is loaded.
For example, with the following document and index:


```sh
127.0.0.1:6379> JSON.SET doc:1 $ '[{"arr": [1, 2, 3]}, {"val": "hello"}, {"val": "world"}]'
OK
127.0.0.1:6379> FT.CREATE idx ON JSON PREFIX 1 doc: SCHEMA $..arr AS arr NUMERIC $..val AS val TEXT
OK
```
Notice the different replies, with and without `DIALECT 3`:

```sh
127.0.0.1:6379> FT.AGGREGATE idx * LOAD 2 arr val 
1) (integer) 1
2) 1) "arr"
   2) "[1,2,3]"
   3) "val"
   4) "hello"

127.0.0.1:6379> FT.AGGREGATE idx * LOAD 2 arr val DIALECT 3
1) (integer) 1
2) 1) "arr"
   2) "[[1,2,3]]"
   3) "val"
   4) "[\"hello\",\"world\"]"
```

## Complexity

Non-deterministic. Depends on the query and aggregations performed, but it is usually linear to the number of results returned.

## Examples

<details open>
<summary><b>Sort page visits by day</b></summary>

Find visits to the page `about.html`, group them by the day of the visit, count the number of visits, and sort them by day.

{{< highlight bash >}}
FT.AGGREGATE idx "@url:\"about.html\""
    APPLY "day(@timestamp)" AS day
    GROUPBY 2 @day @country
      REDUCE count 0 AS num_visits
    SORTBY 4 @day
{{< / highlight >}}
</details>

<details open>
<summary><b>Find most books ever published</b></summary>

Find most books ever published in a single year.

{{< highlight bash >}}
FT.AGGREGATE books-idx *
    GROUPBY 1 @published_year
      REDUCE COUNT 0 AS num_published
    GROUPBY 0
      REDUCE MAX 1 @num_published AS max_books_published_per_year
{{< / highlight >}}
</details>

<details open>
<summary><b>Reduce all results</b></summary>

The last example used `GROUPBY 0`. Use `GROUPBY 0` to apply a `REDUCE` function over all results from the last step of an aggregation pipeline -- this works on both the  initial query and subsequent `GROUPBY` operations.

Search for libraries within 10 kilometers of the longitude -73.982254 and latitude 40.753181 then annotate them with the distance between their location and those coordinates.

{{< highlight bash >}}
 FT.AGGREGATE libraries-idx "@location:[-73.982254 40.753181 10 km]"
    LOAD 1 @location
    APPLY "geodistance(@location, -73.982254, 40.753181)"
{{< / highlight >}}

Here, notice the required use of `LOAD` to pre-load the `@location` attribute because it is a GEO attribute.    

Next, count GitHub events by user (actor), to produce the most active users.

{{< highlight bash >}}
127.0.0.1:6379> FT.AGGREGATE gh "*" GROUPBY 1 @actor REDUCE COUNT 0 AS num SORTBY 2 @num DESC MAX 10
 1) (integer) 284784
 2) 1) "actor"
    2) "lombiqbot"
    3) "num"
    4) "22197"
 3) 1) "actor"
    2) "codepipeline-test"
    3) "num"
    4) "17746"
 4) 1) "actor"
    2) "direwolf-github"
    3) "num"
    4) "10683"
 5) 1) "actor"
    2) "ogate"
    3) "num"
    4) "6449"
 6) 1) "actor"
    2) "openlocalizationtest"
    3) "num"
    4) "4759"
 7) 1) "actor"
    2) "digimatic"
    3) "num"
    4) "3809"
 8) 1) "actor"
    2) "gugod"
    3) "num"
    4) "3512"
 9) 1) "actor"
    2) "xdzou"
    3) "num"
    4) "3216"
[10](10)) 1) "actor"
    2) "opstest"
    3) "num"
    4) "2863"
11) 1) "actor"
    2) "jikker"
    3) "num"
    4) "2794"
(0.59s)
{{< / highlight >}}

</details>

## See also

[`FT.CONFIG SET`](/commands/ft.config-set) | [`FT.SEARCH`](/commands/ft.search) 

## Related topics

- [Aggregations](/docs/interact/search-and-query/search/aggregations)
- [RediSearch](/docs/interact/search-and-query)
# FT.ALTER
## Syntax
```
[SKIPINITIALSCAN] SCHEMA ADD field options```

Add a new attribute to the index. Adding an attribute to the index causes any future document updates to use the new attribute when indexing and reindexing existing documents.

[Examples](#examples)

## Required arguments

<details open>
<summary><code>index</code></summary> 

is index name to create. 
</details>

<details open>
<summary><code>SKIPINITIALSCAN</code></summary> 

if set, does not scan and index.
</details>

<details open>
<summary><code>SCHEMA ADD {attribute} {options} ...</code></summary>

after the SCHEMA keyword, declares which fields to add:

- `attribute` is attribute to add.
- `options` are attribute options. Refer to [`FT.CREATE`](/commands/ft.create) for more information.

<note><b>Note:</b>

Depending on how the index was created, you may be limited by the number of additional text
attributes which can be added to an existing index. If the current index contains fewer than 32
text attributes, then `SCHEMA ADD` will only be able to add attributes up to 32 total attributes (meaning that the
index will only ever be able to contain 32 total text attributes). If you wish for the index to
contain more than 32 attributes, create it with the `MAXTEXTFIELDS` option.
</note>
</details>

## Return

FT.CREATE returns a simple string reply `OK` if executed correctly, or an error reply otherwise.

## Examples

<details open>
<summary><b>Alter an index</b></summary>

{{< highlight bash >}}
127.0.0.1:6379> FT.ALTER idx SCHEMA ADD id2 NUMERIC SORTABLE
OK
{{< / highlight >}}
</details>

## See also

[`FT.CREATE`](/commands/ft.create) 

## Related topics

- [RediSearch](/docs/stack/search)
# FT.CREATE
## Syntax
```
[ON <HASH | JSON>] [PREFIX count prefix [prefix ...]] [FILTER filter] [LANGUAGE default_lang] [LANGUAGE_FIELD lang_attribute] [SCORE default_score] [SCORE_FIELD score_attribute] [PAYLOAD_FIELD payload_attribute] [MAXTEXTFIELDS] [TEMPORARY seconds] [NOOFFSETS] [NOHL] [NOFIELDS] [NOFREQS] [STOPWORDS count [stopword [stopword ...]]] [SKIPINITIALSCAN] SCHEMA field_name [AS alias] <TEXT | TAG | NUMERIC | GEO | VECTOR> [WITHSUFFIXTRIE] [SORTABLE [UNF]] [NOINDEX] [field_name [AS alias] <TEXT | TAG | NUMERIC | GEO | VECTOR> [WITHSUFFIXTRIE] [SORTABLE [UNF]] [NOINDEX] ...]```

## Description

Create an index with the given specification. For usage, see [Examples](#examples).

## Required arguments

<a name="index"></a><details open>
<summary><code>index</code></summary>

is index name to create.
If such index already exists, returns an error reply `(error) Index already exists`.
</details>

<a name="SCHEMA"></a><details open>
<summary><code>SCHEMA {identifier} AS {attribute} {attribute type} {options...</code></summary> 

after the SCHEMA keyword, declares which fields to index:

 - `{identifier}` for hashes, is a field name within the hash.
      For JSON, the identifier is a JSON Path expression.

 - `AS {attribute}` defines the attribute associated to the identifier. For example, you can use this feature to alias a complex JSONPath expression with more memorable (and easier to type) name.

 Field types are:

 - `TEXT` - Allows full-text search queries against the value in this attribute.

 - `TAG` - Allows exact-match queries, such as categories or primary keys, against the value in this attribute. For more information, see [Tag Fields](/docs/interact/search-and-query/advanced-concepts/tags/).

 - `NUMERIC` - Allows numeric range queries against the value in this attribute. See [query syntax docs](/docs/interact/search-and-query/query/) for details on how to use numeric ranges.

 - `GEO` - Allows radius range queries against the value (point) in this attribute. The value of the attribute must be a string containing a longitude (first) and latitude separated by a comma.

 - `VECTOR` - Allows vector queries against the value in this attribute. For more information, see [Vector Fields](/docs/interact/search-and-query/search/vectors/).

 - `GEOSHAPE`- Allows polygon queries against the value in this attribute. The value of the attribute must follow a [WKT notation](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) list of 2D points representing the polygon edges `POLYGON((x1 y1, x2 y2, ...)` separated by a comma. A `GEOSHAPE` field type can be followed by one of the following coordinate systems:
   - `SPHERICAL` for Geographic longitude and latitude coordinates
   - `FLAT` for Cartesian X Y coordinates
  
    The default coordinate system is `SPHERICAL`.
    
    Currently `GEOSHAPE` doesn't support JSON multi-value and `SORTABLE` option.

 Field options are:

 - `SORTABLE` - `NUMERIC`, `TAG`, `TEXT`, or `GEO` attributes can have an optional **SORTABLE** argument. As the user [sorts the results by the value of this attribute](/docs/interact/search-and-query/advanced-concepts/sorting/), the results are available with very low latency. Note that his adds memory overhead, so consider not declaring it on large text attributes. You can sort an attribute without the `SORTABLE` option, but the latency is not as good as with `SORTABLE`.

 - `UNF` - By default, for hashes (not with JSON) `SORTABLE` applies a normalization to the indexed value (characters set to lowercase, removal of diacritics). When using the unnormalized form (UNF), you can disable the normalization and keep the original form of the value. With JSON, `UNF` is implicit with `SORTABLE` (normalization is disabled).

 - `NOSTEM` - Text attributes can have the NOSTEM argument that disables stemming when indexing its values. This may be ideal for things like proper names.

 - `NOINDEX` - Attributes can have the `NOINDEX` option, which means they will not be indexed. This is useful in conjunction with `SORTABLE`, to create attributes whose update using PARTIAL will not cause full reindexing of the document. If an attribute has NOINDEX and doesn't have SORTABLE, it will just be ignored by the index.

 - `PHONETIC {matcher}` - Declaring a text attribute as `PHONETIC` will perform phonetic matching on it in searches by default. The obligatory {matcher} argument specifies the phonetic algorithm and language used. The following matchers are supported:

   - `dm:en` - Double metaphone for English
   - `dm:fr` - Double metaphone for French
   - `dm:pt` - Double metaphone for Portuguese
   - `dm:es` - Double metaphone for Spanish

   For more information, see [Phonetic Matching](/docs/interact/search-and-query/advanced-concepts/phonetic_matching).

  - `WEIGHT {weight}` for `TEXT` attributes, declares the importance of this attribute when calculating result accuracy. This is a multiplication factor, and defaults to 1 if not specified.

  - `SEPARATOR {sep}` for `TAG` attributes, indicates how the text contained in the attribute is to be split into individual tags. The default is `,`. The value must be a single character.

  - `CASESENSITIVE` for `TAG` attributes, keeps the original letter cases of the tags. If not specified, the characters are converted to lowercase.

  - `WITHSUFFIXTRIE` for `TEXT` and `TAG` attributes, keeps a suffix trie with all terms which match the suffix. It is used to optimize `contains` (*foo*) and `suffix` (*foo) queries. Otherwise, a brute-force search on the trie is performed. If suffix trie exists for some fields, these queries will be disabled for other fields.
</details>

## Optional arguments

<a name="ON"></a><details open>
<summary><code>ON {data_type}</code></summary>

currently supports HASH (default) and JSON. To index JSON, you must have the [RedisJSON](/docs/stack/json) module installed.
</details>

<a name="PREFIX"></a><details open>
<summary><code>PREFIX {count} {prefix}</code></summary> 

tells the index which keys it should index. You can add several prefixes to index. Because the argument is optional, the default is `*` (all keys).
</details>

<a name="FILTER"></a><details open>
<summary><code>FILTER {filter}</code></summary> 

is a filter expression with the full RediSearch aggregation expression language. It is possible to use `@__key` to access the key that was just added/changed. A field can be used to set field name by passing `'FILTER @indexName=="myindexname"'`.
</details>

<a name="LANGUAGE"></a><details open>
<summary><code>LANGUAGE {default_lang}</code></summary> 

if set, indicates the default language for documents in the index. Default is English.
</details>

<a name="LANGUAGE_FIELD"></a><details open>
<summary><code>LANGUAGE_FIELD {lang_attribute}</code></summary> 

is document attribute set as the document language.

A stemmer is used for the supplied language during indexing. If an unsupported language is sent, the command returns an error. The supported languages are Arabic, Basque, Catalan, Danish, Dutch, English, Finnish, French, German, Greek, Hungarian,
Indonesian, Irish, Italian, Lithuanian, Nepali, Norwegian, Portuguese, Romanian, Russian,
Spanish, Swedish, Tamil, Turkish, and Chinese.

When adding Chinese language documents, set `LANGUAGE chinese` for the indexer to properly tokenize the terms. If you use the default language, then search terms are extracted based on punctuation characters and whitespace. The Chinese language tokenizer makes use of a segmentation algorithm (via [Friso](https://github.com/lionsoul2014/friso)), which segments text and checks it against a predefined dictionary. See [Stemming](/docs/interact/search-and-query/advanced-concepts/stemming) for more information.
</details>

<a name="SCORE"></a><details open>
<summary><code>SCORE {default_score}</code></summary> 

is default score for documents in the index. Default score is 1.0.
</details>

<a name="SCORE_FIELD"></a><details open>
<summary><code>SCORE_FIELD {score_attribute}</code></summary> 

is document attribute that you use as the document rank based on the user ranking. Ranking must be between 0.0 and 1.0. If not set, the default score is 1.
</details>

<a name="PAYLOAD_FIELD"></a><details open>
<summary><code>PAYLOAD_FIELD {payload_attribute}</code></summary> 

is document attribute that you use as a binary safe payload string to the document that can be evaluated at query time by a custom scoring function or retrieved to the client.
</details>

<a name="MAXTEXTFIELDS"></a><details open>
<summary><code>MAXTEXTFIELDS</code></summary> 

forces RediSearch to encode indexes as if there were more than 32 text attributes, which allows you to add additional attributes (beyond 32) using [`FT.ALTER`](/commands/ft.alter). For efficiency, RediSearch encodes indexes differently if they are created with less than 32 text attributes.
</details>

<a name="NOOFFSETS"></a><details open>
<summary><code>NOOFFSETS</code></summary> 

does not store term offsets for documents. It saves memory, but does not allow exact searches or highlighting. It implies `NOHL`.
</details>

<a name="TEMPORARY"></a><details open>
<summary><code>TEMPORARY {seconds}</code></summary> 

creates a lightweight temporary index that expires after a specified period of inactivity, in seconds. The internal idle timer is reset whenever the index is searched or added to. Because such indexes are lightweight, you can create thousands of such indexes without negative performance implications and, therefore, you should consider using `SKIPINITIALSCAN` to avoid costly scanning.

{{% alert title="Warning" color="warning" %}}
 
When temporary indexes expire, they drop all the records associated with them.
[`FT.DROPINDEX`](/commands/ft.dropindex) was introduced with a default of not deleting docs and a `DD` flag that enforced deletion.
However, for temporary indexes, documents are deleted along with the index.
Historically, RediSearch used an FT.ADD command, which made a connection between the document and the index. Then, FT.DROP, also a hystoric command, deleted documents by default.
In version 2.x, RediSearch indexes hashes and JSONs, and the dependency between the index and documents no longer exists. 

{{% /alert %}}

</details>

<a name="NOHL"></a><details open>
<summary><code>NOHL</code></summary> 

conserves storage space and memory by disabling highlighting support. If set, the corresponding byte offsets for term positions are not stored. `NOHL` is also implied by `NOOFFSETS`.
</details>

<a name="NOFIELDS"></a><details open>
<summary><code>NOFIELDS</code></summary> 

does not store attribute bits for each term. It saves memory, but it does not allow
  filtering by specific attributes.
</details>

<a name="NOFREQS"></a><details open>
<summary><code>NOFREQS</code></summary> 

avoids saving the term frequencies in the index. It saves memory, but does not allow sorting based on the frequencies of a given term within the document.
</details>

<a name="STOPWORDS"></a><details open>
<summary><code>STOPWORDS {count}</code></summary> 

sets the index with a custom stopword list, to be ignored during indexing and search time. `{count}` is the number of stopwords, followed by a list of stopword arguments exactly the length of `{count}`.

If not set, FT.CREATE takes the default list of stopwords. If `{count}` is set to 0, the index does not have stopwords.
</details>

<a name="SKIPINITIALSCAN"></a><details open>
<summary><code>SKIPINITIALSCAN</code></summary> 

if set, does not scan and index.
</details>
        
<note><b>Notes:</b>

 - **Attribute number limits:** RediSearch supports up to 1024 attributes per schema, out of which at most 128 can be TEXT attributes. On 32 bit builds, at most 64 attributes can be TEXT attributes. The more attributes you have, the larger your index, as each additional 8 attributes require one extra byte per index record to encode. You can always use the `NOFIELDS` option and not encode attribute information into the index, for saving space, if you do not need filtering by text attributes. This will still allow filtering by numeric and geo attributes.
 - **Running in clustered databases:** When having several indices in a clustered database, you need to make sure the documents you want to index reside on the same shard as the index. You can achieve this by having your documents tagged by the index name.
    
   {{< highlight bash >}}
   127.0.0.1:6379> HSET doc:1{idx} ...
   127.0.0.1:6379> FT.CREATE idx ... PREFIX 1 doc: ...
   {{< / highlight >}}

   When Running RediSearch in a clustered database, you can span the index across shards using [RSCoordinator](https://github.com/RedisLabsModules/RSCoordinator). In this case the above does not apply.

</note>

## Return

FT.CREATE returns a simple string reply `OK` if executed correctly, or an error reply otherwise.

## Examples

<details open>
<summary><b>Create an index</b></summary>

Create an index that stores the title, publication date, and categories of blog post hashes whose keys start with `blog:post:` (for example, `blog:post:1`).

{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE idx ON HASH PREFIX 1 blog:post: SCHEMA title TEXT SORTABLE published_at NUMERIC SORTABLE category TAG SORTABLE
OK
{{< / highlight >}}

Index the `sku` attribute from a hash as both a `TAG` and as `TEXT`:

{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE idx ON HASH PREFIX 1 blog:post: SCHEMA sku AS sku_text TEXT sku AS sku_tag TAG SORTABLE
{{< / highlight >}}

Index two different hashes, one containing author data and one containing books, in the same index:

{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE author-books-idx ON HASH PREFIX 2 author:details: book:details: SCHEMA
author_id TAG SORTABLE author_ids TAG title TEXT name TEXT
{{< / highlight >}}

In this example, keys for author data use the key pattern `author:details:<id>` while keys for book data use the pattern `book:details:<id>`.
</details>

<details open>
<summary><b>Index a JSON document using a JSON Path expression</b></summary>

Index authors whose names start with G.

{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE g-authors-idx ON HASH PREFIX 1 author:details FILTER 'startswith(@name, "G")' SCHEMA name TEXT
{{< / highlight >}}

Index only books that have a subtitle.

{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE subtitled-books-idx ON HASH PREFIX 1 book:details FILTER '@subtitle != ""' SCHEMA title TEXT
{{< / highlight >}}

Index books that have a "categories" attribute where each category is separated by a `;` character.

{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE books-idx ON HASH PREFIX 1 book:details FILTER SCHEMA title TEXT categories TAG SEPARATOR ";"
{{< / highlight >}}

Index a JSON document using a JSON Path expression.

{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE idx ON JSON SCHEMA $.title AS title TEXT $.categories AS categories TAG
{{< / highlight >}}
</details>

## See also

[`FT.ALTER`](/commands/ft.alter) | [`FT.DROPINDEX`](/commands/ft.dropindex) 

## Related topics

- [RediSearch](/docs/stack/search)
- [RedisJSON](/docs/stack/json)
- [Friso](https://github.com/lionsoul2014/friso)
- [Stemming](/docs/interact/search-and-query/advanced-concepts/stemming)
- [Phonetic Matching](/docs/interact/search-and-query/advanced-concepts/phonetic_matching/)
- [RSCoordinator](https://github.com/RedisLabsModules/RSCoordinator)
# FT.CURSOR DEL
## Syntax
```
cursor_id```

Delete a cursor

[Examples](#examples)

## Required arguments

<details open>
<summary><code>index</code></summary>

is index name.
</details>

<details open>
<summary><code>cursor_id</code></summary>

is id of the cursor.
</details>

## Returns

FT.CURSOR DEL returns a simple string reply `OK` if executed correctly, or an error reply otherwise.

## Examples

<details open>
<summary><b>Delete a cursor</b></summary>

{{< highlight bash >}}
redis> FT.CURSOR DEL idx 342459320
OK
{{< / highlight >}}

Check that the cursor is deleted.

{{< highlight bash >}}
127.0.0.1:6379> FT.CURSOR DEL idx 342459320
(error) Cursor does not exist
{{< / highlight >}}
</details>

## See also

[`FT.CURSOR READ`](/commands/ft.cursor-read) 

## Related topics

[RediSearch](/docs/stack/search)
# FT.CURSOR READ
## Syntax
```
cursor_id [COUNT read size]```

Read next results from an existing cursor

[Examples](#examples)

See [Cursor API](/docs/stack/search/reference/aggregations/#cursor-api) for more details.

## Required arguments

<details open>
<summary><code>index</code></summary>

is index name.
</details>

<details open>
<summary><code>cursor_id</code></summary>

is id of the cursor.
</details>

<details open>
<summary><code>[COUNT read_size]</code></summary>

is number of results to read. This parameter overrides `COUNT` specified in [`FT.AGGREGATE`](/commands/ft.aggregate).
</details>

## Return

FT.CURSOR READ returns an array reply where each row is an array reply and represents a single aggregate result.

## Examples

<details open>
<summary><b>Read next results from a cursor</b></summary>

{{< highlight bash >}}
127.0.0.1:6379> FT.CURSOR READ idx 342459320 COUNT 50
{{< / highlight >}}
</details>

## See also

[`FT.CURSOR DEL`](/commands/ft.cursor-del) | [`FT.AGGREGATE`](/commands/ft.aggregate)

## Related topics

[RediSearch](/docs/stack/search)
# FT.DROPINDEX
## Syntax
```
[DD]```

Delete an index

[Examples](#examples)

## Required arguments

<details open>
<summary><code>index</code></summary>

is full-text index name. You must first create the index using [`FT.CREATE`](/commands/ft.create).
</details>

## Optional arguments

<details open>
<summary><code>DD</code></summary>

drop operation that, if set, deletes the actual document hashes.

By default, FT.DROPINDEX does not delete the documents associated with the index. Adding the `DD` option deletes the documents as well. 
If an index creation is still running ([`FT.CREATE`](/commands/ft.create) is running asynchronously), only the document hashes that have already been indexed are deleted. 
The document hashes left to be indexed remain in the database.
To check the completion of the indexing, use [`FT.INFO`](/commands/ft.info).

</details>

## Return

FT.DROPINDEX returns a simple string reply `OK` if executed correctly, or an error reply otherwise.

## Examples

<details open>
<summary><b>Delete an index</b></summary>

{{< highlight bash >}}
127.0.0.1:6379> FT.DROPINDEX idx DD
OK
{{< / highlight >}}
</details>

## See also

[`FT.CREATE`](/commands/ft.create) | [`FT.INFO`](/commands/ft.info)

## Related topics

[RediSearch](/docs/stack/search)
# FT.EXPLAIN
## Syntax
```
query [DIALECT dialect]```

Return the execution plan for a complex query

[Examples](#examples)

## Required arguments

<details open>
<summary><code>index</code></summary>

is index name. You must first create the index using [`FT.CREATE`](/commands/ft.create).
</details>

<details open>
<summary><code>query</code></summary>

is query string, as if sent to FT.SEARCH`.
</details>

## Optional arguments

<details open>
<summary><code>DIALECT {dialect_version}</code></summary>

is dialect version under which to execute the query. If not specified, the query executes under the default dialect version set during module initial loading or via [`FT.CONFIG SET`](/commands/ft.config-set) command.
</details>

{{% alert title="Notes" color="warning" %}}
 
- In the returned response, a `+` on a term is an indication of stemming.
- Use `redis-cli --raw` to properly read line-breaks in the returned response.

{{% /alert %}}

## Return

FT.EXPLAIN returns a string representing the execution plan.

## Examples

<details open>
<summary><b>Return the execution plan for a complex query</b></summary>

{{< highlight bash >}}
$ redis-cli --raw

127.0.0.1:6379> FT.EXPLAIN rd "(foo bar)|(hello world) @date:[100 200]|@date:[500 +inf]"
INTERSECT {
  UNION {
    INTERSECT {
      foo
      bar
    }
    INTERSECT {
      hello
      world
    }
  }
  UNION {
    NUMERIC {100.000000 <= x <= 200.000000}
    NUMERIC {500.000000 <= x <= inf}
  }
}
{{< / highlight >}}
</details>

## See also

[`FT.CREATE`](/commands/ft.create) | [`FT.SEARCH`](/commands/ft.search) | [`FT.CONFIG SET`](/commands/ft.config-set)

## Related topics

[RediSearch](/docs/stack/search)
# FT.INFO
## Syntax
```
```

Return information and statistics on the index

[Examples](#examples)

## Required arguments

<details open>
<summary><code>index</code></summary>

is full-text index name. You must first create the index using [`FT.CREATE`](/commands/ft.create).
</details>

## Return

FT.INFO returns an array reply with pairs of keys and values.

Returned values include:

- `index_definition`: reflection of [`FT.CREATE`](/commands/ft.create) command parameters.
- `fields`: index schema - field names, types, and attributes.
- Number of documents.
- Number of distinct terms.
- Average bytes per record.
- Size and capacity of the index buffers.
- Indexing state and percentage as well as failures:
  - `indexing`: whether of not the index is being scanned in the background.
  - `percent_indexed`: progress of background indexing (1 if complete).
  - `hash_indexing_failures`: number of failures due to operations not compatible with index schema.

Optional statistics include:

* `garbage collector` for all options other than NOGC.
* `cursors` if a cursor exists for the index.
* `stopword lists` if a custom stopword list is used.

## Examples

<details open>
<summary><b>Return statistics about an index</b></summary>

{{< highlight bash >}}
127.0.0.1:6379> FT.INFO idx
1) index_name
 2) wikipedia
 3) index_options
 4) (empty array)
    11) score_field
    12) __score
    13) payload_field
    14) __payload
 7) fields
 8) 1) 1) title
       2) type
       3) TEXT
       4) WEIGHT
       5) "1"
       6) SORTABLE
    2) 1) body
       2) type
       3) TEXT
       4) WEIGHT
       5) "1"
    3) 1) id
       2) type
       3) NUMERIC
    4) 1) subject location
       2) type
       3) GEO
 9) num_docs
10) "0"
11) max_doc_id
12) "345678"
13) num_terms
14) "691356"
15) num_records
16) "0"
17) inverted_sz_mb
18) "0"
19) vector_index_sz_mb
20) "0"
21) total_inverted_index_blocks
22) "933290"
23) offset_vectors_sz_mb
24) "0.65932846069335938"
25) doc_table_size_mb
26) "29.893482208251953"
27) sortable_values_size_mb
28) "11.432285308837891"
29) key_table_size_mb
30) "1.239776611328125e-05"
31) records_per_doc_avg
32) "-nan"
33) bytes_per_record_avg
34) "-nan"
35) offsets_per_term_avg
36) "inf"
37) offset_bits_per_record_avg
38) "8"
39) hash_indexing_failures
40) "0"
41) indexing
42) "0"
43) percent_indexed
44) "1"
45) number_of_uses
46) 1
47) gc_stats
48)  1) bytes_collected
     2) "4148136"
     3) total_ms_run
     4) "14796"
     5) total_cycles
     6) "1"
     7) average_cycle_time_ms
     8) "14796"
     9) last_run_time_ms
    10) "14796"
    11) gc_numeric_trees_missed
    12) "0"
    13) gc_blocks_denied
    14) "0"
49) cursor_stats
50) 1) global_idle
    2) (integer) 0
    3) global_total
    4) (integer) 0
    5) index_capacity
    6) (integer) 128
    7) index_total
    8) (integer) 0
51) stopwords_list
52) 1) "tlv"
    2) "summer"
    3) "2020"
{{< / highlight >}}
</details>

## See also

[`FT.CREATE`](/commands/ft.create) | [`FT.SEARCH`](/commands/ft.search)

## Related topics

[RediSearch](/docs/stack/search)
# FT.PROFILE
## Syntax
```
<SEARCH | AGGREGATE> [LIMITED] QUERY query```

Apply [`FT.SEARCH`](/commands/ft.search) or [`FT.AGGREGATE`](/commands/ft.aggregate) command to collect performance details

[Examples](#examples)

## Required arguments

<details open>
<summary><code>index</code></summary>

is index name, created using [`FT.CREATE`](/commands/ft.create).
</details>

<details open>
<summary><code>SEARCH | AGGREGATE</code></summary>

is difference between [`FT.SEARCH`](/commands/ft.search) and [`FT.AGGREGATE`](/commands/ft.aggregate).
</details>

<details open>
<summary><code>LIMITED</code></summary>

removes details of `reader` iterator.
</details>

<details open>
<summary><code>QUERY {query}</code></summary>

is query string, sent to [`FT.SEARCH`](/commands/ft.search).
</details>

<note><b>Note:</b> To reduce the size of the output, use `NOCONTENT` or `LIMIT 0 0` to reduce the reply results or `LIMITED` to not reply with details of `reader iterators` inside built-in unions such as `fuzzy` or `prefix`.</note>

## Return

`FT.PROFILE` returns an array reply, with the first array reply identical to the reply of [`FT.SEARCH`](/commands/ft.search) and [`FT.AGGREGATE`](/commands/ft.aggregate) and a second array reply with information of time in milliseconds (ms) used to create the query and time and count of calls of iterators and result-processors.

Return value has an array with two elements:

- Results - The normal reply from RediSearch, similar to a cursor.
- Profile - The details in the profile are:
  - Total profile time - The total runtime of the query, in ms.
  - Parsing time - Parsing time of the query and parameters into an execution plan, in ms.
  - Pipeline creation time - Creation time of execution plan including iterators,
  result processors, and reducers creation, in ms.
  - Iterators profile - Index iterators information including their type, term, count, and time data.
  Inverted-index iterators have in addition the number of elements they contain. Hybrid vector iterators returning the top results from the vector index in batches, include the number of batches.
  - Result processors profile - Result processors chain with type, count, and time data.

## Examples

<details open>
<summary><b>Collect performance information about an index</b></summary>

{{< highlight bash >}}
127.0.0.1:6379> FT.PROFILE idx SEARCH QUERY "hello world"
1) 1) (integer) 1
   2) "doc1"
   3) 1) "t"
      2) "hello world"
2) 1) 1) Total profile time
      2) "0.47199999999999998"
   2) 1) Parsing time
      2) "0.218"
   3) 1) Pipeline creation time
      2) "0.032000000000000001"
   4) 1) Iterators profile
      2) 1) Type
         2) INTERSECT
         3) Time
         4) "0.025000000000000001"
         5) Counter
         6) (integer) 1
         7) Child iterators
         8)  1) Type
             2) TEXT
             3) Term
             4) hello
             5) Time
             6) "0.0070000000000000001"
             7) Counter
             8) (integer) 1
             9) Size
            10) (integer) 1
         9)  1) Type
             2) TEXT
             3) Term
             4) world
             5) Time
             6) "0.0030000000000000001"
             7) Counter
             8) (integer) 1
             9) Size
            10) (integer) 1
   5) 1) Result processors profile
      2) 1) Type
         2) Index
         3) Time
         4) "0.036999999999999998"
         5) Counter
         6) (integer) 1
      3) 1) Type
         2) Scorer
         3) Time
         4) "0.025000000000000001"
         5) Counter
         6) (integer) 1
      4) 1) Type
         2) Sorter
         3) Time
         4) "0.013999999999999999"
         5) Counter
         6) (integer) 1
      5) 1) Type
         2) Loader
         3) Time
         4) "0.10299999999999999"
         5) Counter
         6) (integer) 1
{{< / highlight >}}
</details>

## See also

[`FT.SEARCH`](/commands/ft.search) | [`FT.AGGREGATE`](/commands/ft.aggregate) 

## Related topics

[RediSearch](/docs/stack/search)
# FT.SEARCH
## Syntax
```
query [NOCONTENT] [VERBATIM] [NOSTOPWORDS] [WITHSCORES] [WITHPAYLOADS] [WITHSORTKEYS] [FILTER numeric_field min max [FILTER numeric_field min max ...]] [GEOFILTER geo_field lon lat radius <m | km | mi | ft> [GEOFILTER geo_field lon lat radius <m | km | mi | ft> ...]] [INKEYS count key [key ...]] [INFIELDS count field [field ...]] [RETURN count identifier [AS property] [identifier [AS property] ...]] [SUMMARIZE [FIELDS count field [field ...]] [FRAGS num] [LEN fragsize] [SEPARATOR separator]] [HIGHLIGHT [FIELDS count field [field ...]] [TAGS open close]] [SLOP slop] [TIMEOUT timeout] [INORDER] [LANGUAGE language] [EXPANDER expander] [SCORER scorer] [EXPLAINSCORE] [PAYLOAD payload] [SORTBY sortby [ASC | DESC]] [LIMIT offset num] [PARAMS nargs name value [name value ...]] [DIALECT dialect]```

Search the index with a textual query, returning either documents or just ids

[Examples](#examples)

## Required arguments

<details open>
<summary><code>index</code></summary>

is index name. You must first create the index using [`FT.CREATE`](/commands/ft.create).
</details>

<details open>
<summary><code>query</code></summary> 

is text query to search. If it's more than a single word, put it in quotes. Refer to [Query syntax](/docs/interact/search-and-query/query/) for more details.
</details>

## Optional arguments

<details open>
<summary><code>NOCONTENT</code></summary>

returns the document ids and not the content. This is useful if RediSearch is only an index on an external document collection.
</details>

<details open>
<summary><code>VERBATIM</code></summary>

does not try to use stemming for query expansion but searches the query terms verbatim.
</details>

<details open>
<summary><code>WITHSCORES</code></summary>

also returns the relative internal score of each document. This can be used to merge results from multiple instances.
</details>

<details open>
<summary><code>WITHPAYLOADS</code></summary>

retrieves optional document payloads. See [`FT.CREATE`](/commands/ft.create). The payloads follow the document id and, if `WITHSCORES` is set, the scores.
</details>

<details open>
<summary><code>WITHSORTKEYS</code></summary>

returns the value of the sorting key, right after the id and score and/or payload, if requested. This is usually not needed, and exists for distributed search coordination purposes. This option is relevant only if used in conjunction with `SORTBY`.
</details>

<details open>
<summary><code>FILTER numeric_attribute min max</code></summary>

limits results to those having numeric values ranging between `min` and `max`, if numeric_attribute is defined as a numeric attribute in [`FT.CREATE`](/commands/ft.create). 
  `min` and `max` follow [`ZRANGE`](/commands/zrange) syntax, and can be `-inf`, `+inf`, and use `(` for exclusive ranges. Multiple numeric filters for different attributes are supported in one query.
</details>

<details open>
<summary><code>GEOFILTER {geo_attribute} {lon} {lat} {radius} m|km|mi|ft</code></summary>

filter the results to a given `radius` from `lon` and `lat`. Radius is given as a number and units. See [`GEORADIUS`](/commands/georadius) for more details.
</details>

<details open>
<summary><code>INKEYS {num} {attribute} ...</code></summary>

limits the result to a given set of keys specified in the list. The first argument must be the length of the list and greater than zero. Non-existent keys are ignored, unless all the keys are non-existent.
</details>

<details open>
<summary><code>INFIELDS {num} {attribute} ...</code></summary>

filters the results to those appearing only in specific attributes of the document, like `title` or `URL`. You must include `num`, which is the number of attributes you're filtering by. For example, if you request `title` and `URL`, then `num` is 2.
</details>

<details open>
<summary><code>RETURN {num} {identifier} AS {property} ...</code></summary>

limits the attributes returned from the document. `num` is the number of attributes following the keyword. If `num` is 0, it acts like `NOCONTENT`.
  `identifier` is either an attribute name (for hashes and JSON) or a JSON Path expression (for JSON).
  `property` is an optional name used in the result. If not provided, the `identifier` is used in the result.
</details>

<details open>
<summary><code>SUMMARIZE ...</code></summary>

returns only the sections of the attribute that contain the matched text. See [Highlighting](/docs/interact/search-and-query/advanced-concepts/highlight/) for more information.
</details>

<details open>
<summary><code>HIGHLIGHT ...</code></summary>

formats occurrences of matched text. See [Highlighting](/docs/interact/search-and-query/advanced-concepts/highlight/) for more information.
</details>

<details open>
<summary><code>SLOP {slop}</code></summary>

is the number of intermediate terms allowed to appear between the terms of the query. 
Suppose you're searching for a phrase _hello world_.
If some terms appear in-between _hello_ and _world_, a `SLOP` greater than `0` allows for these text attributes to match.
By default, there is no `SLOP` constraint.
</details>

<details open>
<summary><code>INORDER</code></summary>

requires the terms in the document to have the same order as the terms in the query, regardless of the offsets between them. Typically used in conjunction with `SLOP`. Default is `false`.

</details>

<details open>
<summary><code>LANGUAGE {language}</code></summary>

use a stemmer for the supplied language during search for query expansion. If querying documents in Chinese, set to `chinese` to
  properly tokenize the query terms. Defaults to English. If an unsupported language is sent, the command returns an error.
  See [`FT.CREATE`](/commands/ft.create) for the list of languages. 
</details>

<details open>
<summary><code>EXPANDER {expander}</code></summary>

uses a custom query expander instead of the stemmer. See [Extensions](/docs/interact/search-and-query/administration/extensions/).
</details>

<details open>
<summary><code>SCORER {scorer}</code></summary>

uses a [built-in](/docs/interact/search-and-query/advanced-concepts/scoring/) or a [user-provided](/docs/interact/search-and-query/administration/extensions/) scoring function.
</details>

<details open>
<summary><code>EXPLAINSCORE</code></summary>

returns a textual description of how the scores were calculated. Using this option requires `WITHSCORES`.
</details>

<details open>
<summary><code>PAYLOAD {payload}</code></summary>

adds an arbitrary, binary safe payload that is exposed to custom scoring functions. See [Extensions](/docs/interact/search-and-query/administration/extensions/).
</details>

<details open>
<summary><code>SORTBY {attribute} [ASC|DESC] [WITHCOUNT]</code></summary>

orders the results by the value of this attribute. This applies to both text and numeric attributes. Attributes needed for `SORTBY` should be declared as `SORTABLE` in the index, in order to be available with very low latency. Note that this adds memory overhead.

**Sorting Optimizations**: performance is optimized for sorting operations on `DIALECT 4` in different scenarios:
  - Skip Sorter - applied when there is no sort of any kind. The query can return after it reaches the `LIMIT` requested results.
  - Partial Range - applied when there is a `SORTBY` clause over a numeric field, with no filter or filter by the same numeric field, the query iterate on a range large enough to satisfy the `LIMIT` requested results.
  - Hybrid - applied when there is a `SORTBY` clause over a numeric field and another non-numeric filter. Some results will get filtered, and the initial range may not be large enough. The iterator is then rewinding with the following ranges, and an additional iteration takes place to collect the `LIMIT` requested results.
  - No optimization - If there is a sort by score or by non-numeric field, there is no other option but to retrieve all results and compare their values.

**Counts behavior**: optional`WITHCOUNT`argument returns accurate counts for the query results with sorting. This operation processes all results in order to get an accurate count, being less performant than the optimized option (default behavior on `DIALECT 4`)


</details>

<details open>
<summary><code>LIMIT first num</code></summary>

limits the results to the offset and number of results given. Note that the offset is zero-indexed. The default is 0 10, which returns 10 items starting from the first result. You can use `LIMIT 0 0` to count the number of documents in the result set without actually returning them.
</details>

<details open>
<summary><code>TIMEOUT {milliseconds}</code></summary>

overrides the timeout parameter of the module.
</details>

<details open>
<summary><code>PARAMS {nargs} {name} {value}</code></summary>

defines one or more value parameters. Each parameter has a name and a value. 

You can reference parameters in the `query` by a `$`, followed by the parameter name, for example, `$user`. Each such reference in the search query to a parameter name is substituted by the corresponding parameter value. For example, with parameter definition `PARAMS 4 lon 29.69465 lat 34.95126`, the expression `@loc:[$lon $lat 10 km]` is evaluated to `@loc:[29.69465 34.95126 10 km]`. You cannot reference parameters in the query string where concrete values are not allowed, such as in field names, for example, `@loc`. To use `PARAMS`, set `DIALECT` to `2` or greater than `2`.
</details>

<details open>
<summary><code>DIALECT {dialect_version}</code></summary>

selects the dialect version under which to execute the query. If not specified, the query will execute under the default dialect version set during module initial loading or via [`FT.CONFIG SET`](/commands/ft.config-set) command.
</details>

## Return

FT.SEARCH returns an array reply, where the first element is an integer reply of the total number of results, and then array reply pairs of document ids, and array replies of attribute/value pairs.

{{% alert title="Notes" color="warning" %}}
 
- If `NOCONTENT` is given, an array is returned where the first element is the total number of results, and the rest of the members are document ids.
- If a hash expires after the query process starts, the hash is counted in the total number of results, but the key name and content return as null.

{{% /alert %}}

### Return multiple values

When the index is defined `ON JSON`, a reply for a single attribute or a single JSONPath may return multiple values when the JSONPath matches multiple values, or when the JSONPath matches an array.

Prior to RediSearch v2.6, only the first of the matched values was returned.
Starting with RediSearch v2.6, all values are returned, wrapped with a top-level array.

In order to maintain backward compatibility, the default behavior with RediSearch v2.6 is to return only the first value.

To return all the values, use `DIALECT` 3 (or greater, when available).

The `DIALECT` can be specified as a parameter in the FT.SEARCH command. If it is not specified, the `DEFAULT_DIALECT` is used, which can be set using [`FT.CONFIG SET`](/commands/ft.config-set) or by passing it as an argument to the `redisearch` module when it is loaded.

For example, with the following document and index:


```sh
127.0.0.1:6379> JSON.SET doc:1 $ '[{"arr": [1, 2, 3]}, {"val": "hello"}, {"val": "world"}]'
OK
127.0.0.1:6379> FT.CREATE idx ON JSON PREFIX 1 doc: SCHEMA $..arr AS arr NUMERIC $..val AS val TEXT
OK
```
Notice the different replies, with and without `DIALECT 3`:

```sh
127.0.0.1:6379> FT.SEARCH idx * RETURN 2 arr val
1) (integer) 1
2) "doc:1"
3) 1) "arr"
   2) "[1,2,3]"
   3) "val"
   4) "hello"

127.0.0.1:6379> FT.SEARCH idx * RETURN 2 arr val DIALECT 3
1) (integer) 1
2) "doc:1"
3) 1) "arr"
   2) "[[1,2,3]]"
   3) "val"
   4) "[\"hello\",\"world\"]"
```

## Complexity

FT.SEARCH complexity is O(n) for single word queries. `n` is the number of the results in the result set. Finding all the documents that have a specific term is O(1), however, a scan on all those documents is needed to load the documents data from redis hashes and return them.

The time complexity for more complex queries varies, but in general it's proportional to the number of words, the number of intersection points between them and the number of results in the result set.

## Examples

<details open>
<summary><b>Search for a term in every text attribute</b></summary>

Search for the term "wizard" in every TEXT attribute of an index containing book data.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "wizard"
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a term in title attribute</b></summary>

Search for the term _dogs_ in the `title` attribute.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "@title:dogs"
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for books from specific years</b></summary>

Search for books published in 2020 or 2021.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "@published_at:[2020 2021]"
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a restaurant by distance from longitude/latitude</b></summary>

Search for Chinese restaurants within 5 kilometers of longitude -122.41, latitude 37.77 (San Francisco).

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH restaurants-idx "chinese @location:[-122.41 37.77 5 km]"
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a book by terms but boost specific term</b></summary>

Search for the term _dogs_ or _cats_ in the `title` attribute, but give matches of _dogs_ a higher relevance score (also known as _boosting_).

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "(@title:dogs | @title:cats) | (@title:dogs) => { $weight: 5.0; }"
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a book by a term and EXPLAINSCORE</b></summary>

Search for books with _dogs_ in any TEXT attribute in the index and request an explanation of scoring for each result.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "dogs" WITHSCORES EXPLAINSCORE
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a book by a term and TAG</b></summary>

Search for books with _space_ in the title that have `science` in the TAG attribute `categories`.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "@title:space @categories:{science}"
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a book by a term but limit the number</b></summary>

Search for books with _Python_ in any `TEXT` attribute, returning 10 results starting with the 11th result in the entire result set (the offset parameter is zero-based), and return only the `title` attribute for each result.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "python" LIMIT 10 10 RETURN 1 title
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a book by a term and price</b></summary>

Search for books with _Python_ in any `TEXT` attribute, returning the price stored in the original JSON document.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "python" RETURN 3 $.book.price AS price
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a book by title and distance</b></summary>

Search for books with semantically similar title to _Planet Earth_. Return top 10 results sorted by distance.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH books-idx "*=>[KNN 10 @title_embedding $query_vec AS title_score]" PARAMS 2 query_vec <"Planet Earth" embedding BLOB> SORTBY title_score DIALECT 2
{{< / highlight >}}
</details>

<details open>
<summary><b>Search for a phrase using SLOP</b></summary>

Search for a phrase _hello world_.
First, create an index.

{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE memes SCHEMA phrase TEXT
OK
{{< / highlight >}}

Add variations of the phrase _hello world_.

{{< highlight bash >}}
127.0.0.1:6379> HSET s1 phrase "hello world"
(integer) 1
127.0.0.1:6379> HSET s2 phrase "hello simple world"
(integer) 1
127.0.0.1:6379> HSET s3 phrase "hello somewhat less simple world"
(integer) 1
127.0.0.1:6379> HSET s4 phrase "hello complicated yet encouraging problem solving world"
(integer) 1
127.0.0.1:6379> HSET s5 phrase "hello complicated yet amazingly encouraging problem solving world"
(integer) 1
{{< / highlight >}}

Then, search for the phrase _hello world_. The result returns all documents that contain the phrase.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(hello world)' NOCONTENT 
1) (integer) 5
2) "s1"
3) "s2"
4) "s3"
5) "s4"
6) "s5"
{{< / highlight >}}

Now, return all documents that have one of fewer words between _hello_ and _world_.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(hello world)' NOCONTENT SLOP 1
1) (integer) 2
2) "s1"
3) "s2"
{{< / highlight >}}

Now, return all documents with three or fewer words between _hello_ and _world_.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(hello world)' NOCONTENT SLOP 3
1) (integer) 3
2) "s1"
3) "s2"
4) "s3"
{{< / highlight >}}

`s5` needs a higher `SLOP` to match, `SLOP 6` or higher, to be exact. See what happens when you set `SLOP` to `5`.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(hello world)' NOCONTENT SLOP 5
1) (integer) 4
2) "s1"
3) "s2"
4) "s3"
5) "s4"
{{< / highlight >}}

If you add additional terms (and stemming), you get these results.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(hello amazing world)' NOCONTENT 
1) (integer) 1
2) "s5"
{{< / highlight >}}

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(hello encouraged world)' NOCONTENT SLOP 5
1) (integer) 2
2) "s4"
3) "s5"
{{< / highlight >}}

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(hello encouraged world)' NOCONTENT SLOP 4
1) (integer) 1
2) "s4"
{{< / highlight >}}

If you swap the terms, you can still retrieve the correct phrase.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(amazing hello world)' NOCONTENT
1) (integer) 1
2) "s5"
{{< / highlight >}}

But, if you use `INORDER`, you get zero results.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(amazing hello world)' NOCONTENT INORDER
1) (integer) 0
{{< / highlight >}}

Likewise, if you use a query attribute `$inorder` set to `true`, `s5` is not retrieved.

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH memes '@phrase:(amazing hello world)=>{$inorder: true;}' NOCONTENT
1) (integer) 0
{{< / highlight >}}

To sum up, the `INORDER` argument or `$inorder` query attribute require the query terms to match terms with similar ordering.

</details>

<details open>
<summary><b>NEW!!! Polygon Search with WITHIN and CONTAINS operators</b></summary>

Query for polygons which contain a given geoshape or are within a given geoshape

First, create an index using `GEOSHAPE` type with a `FLAT` coordinate system:


{{< highlight bash >}}
127.0.0.1:6379> FT.CREATE idx SCHEMA geom GEOSHAPE FLAT
OK
{{< / highlight >}}

Adding a couple of geometries using [`HSET`](/commands/hset):


{{< highlight bash >}}
127.0.0.1:6379> HSET small geom 'POLYGON((1 1, 1 100, 100 100, 100 1, 1 1))'
(integer) 1
127.0.0.1:6379> HSET large geom 'POLYGON((1 1, 1 200, 200 200, 200 1, 1 1))'
(integer) 1
{{< / highlight >}}

Query with `WITHIN` operator:

{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH idx '@geom:[WITHIN $poly]' PARAMS 2 poly 'POLYGON((0 0, 0 150, 150 150, 150 0, 0 0))' DIALECT 3

1) (integer) 1
2) "small"
3) 1) "geom"
   2) "POLYGON((1 1, 1 100, 100 100, 100 1, 1 1))"
{{< / highlight >}}

Query with `CONTAINS` operator:


{{< highlight bash >}}
127.0.0.1:6379> FT.SEARCH idx '@geom:[CONTAINS $poly]' PARAMS 2 poly 'POLYGON((2 2, 2 50, 50 50, 50 2, 2 2))' DIALECT 3

1) (integer) 2
2) "small"
3) 1) "geom"
   2) "POLYGON((1 1, 1 100, 100 100, 100 1, 1 1))"
4) "large"
5) 1) "geom"
   2) "POLYGON((1 1, 1 200, 200 200, 200 1, 1 1))"
{{< / highlight >}}

</details>

## See also

[`FT.CREATE`](/commands/ft.create) | [`FT.AGGREGATE`](/commands/ft.aggregate) 

## Related topics

- [Extensions](/docs/interact/search-and-query/administration/extensions/)
- [Highlighting](/docs/interact/search-and-query/advanced-concepts/highlight/)
- [Query syntax](/docs/interact/search-and-query/query/)
- [RediSearch](/docs/stack/search)
