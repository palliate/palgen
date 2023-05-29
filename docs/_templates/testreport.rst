**Test file**: {file}

.. git_commit_detail::
    :branch:
    :commit:
    :sha_length: 7

**Statistics**

| Test suites: :need_count:`'{id}' in tags and type=='{suite_need}'`
| Test cases: :need_count:`'{id}' in tags and type=='{case_need}'`
| Failed test cases: :need_count:`'{id}' in tags and 'failure' == result and type=='{case_need}'`
| Skipped test cases: :need_count:`'{id}' in tags and 'skipped' == result and type=='{case_need}'`

**Test cases**:

.. needtable::
   :filter: '{id}' in tags and type == '{case_need}'
   :columns: id, title, result
   :style_row: tr_[[copy('result')]]

**Failed test cases**:

.. needtable::
   :filter: '{id}' in tags and 'failure' == result
   :columns: id, title, result
   :style_row: tr_[[copy('result')]]

**Skipped test cases**:

.. needtable::
   :filter: '{id}' in tags and 'skipped' == result
   :columns: id, title, result
   :style_row: tr_[[copy('result')]]

**Imported data**


.. {file_type}:: {title}
   :id: {id}{links_string}
   :tags: {tags}
   :file: {file}
   :auto_suites:
   :auto_cases:

   {content}

