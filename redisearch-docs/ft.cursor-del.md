---
arguments:
- name: index
  type: string
- name: cursor_id
  type: integer
complexity: O(1)
description: Deletes a cursor
github_branch: master
github_path: docs/commands/ft.cursor-del.md
github_repo: https://github.com/redisearch/redisearch
group: search
hidden: false
linkTitle: FT.CURSOR DEL
module: Search
since: 1.1.0
stack_path: docs/interact/search-and-query
summary: Deletes a cursor
syntax: 'FT.CURSOR DEL index cursor_id

  '
syntax_fmt: FT.CURSOR DEL index cursor_id
syntax_str: cursor_id
title: FT.CURSOR DEL
---

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