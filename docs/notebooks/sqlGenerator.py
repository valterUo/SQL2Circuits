import random
import json
from itertools import combinations
dtype_samples = {"str": "abc", "int": 99999, "float": 99999.1, "time": "00:00:00", "date": "2023-01-01"}

class SQLGenerator:
  # Initializer sets up database config and tables/relations data
  def __init__(self, db_config_file=None, seed=1234):
    self.seed = seed
    if db_config_file == None:
      print("No database config specified. Using default...")
      self.db_config_file="database.json"
    else: 
      self.db_config_file=db_config_file
    with open(db_config_file, 'r') as f:
      tables_dict = json.load(f)
    self._setTableData(tables_dict)
    random.seed(self.seed)
  
  # Set table data pertaining to database
  def _setTableData(self, tables_dict):
    self.tables = tables_dict
    table_names = tables_dict.keys()
    # Set up pairs of tables
    table_combs = combinations(table_names, 2)
    # A valid relation is one that contains/equals the variables below
    allow_equals = set(['year','lap'])
    allow_contains = set(['id'])
    conditions = dict()
    # For every pair of tables, find if there is a valid relation
    for table_pair in table_combs:
      table1 = table_pair[0]
      table1_cols = tables_dict[table1][0]
      table1_dtypes = tables_dict[table1][1]
      table2 = table_pair[1]
      table2_cols = tables_dict[table2][0]
      col_set = set(table1_cols).intersection(table2_cols)
      valid_relations = set()
      # Loop over columns in intersection of table cols and find valid
      # columns that are common to both
      for col in col_set:
        is_valid = False
        for string in allow_contains:
          if string in col:
            is_valid = True
            break
        if is_valid or col.lower() in allow_equals:
          valid_relations.add(col)
      if valid_relations == set():
        continue
      conditions[(table1, table2)] = []
      # Set up condition format and add to dict
      for col in valid_relations:
        dtype_index = table1_cols.index(col)
        conditions[(table1, table2)].append((table1 + "." + col + "=" + table2 + "." + col, table1_dtypes[dtype_index]))
    self.relations = conditions
  
  # Generates possible joins for current table data in database
  # This ensures there are relationships in between tables so conditions can
  # be created in between the tables that are in a generated query
  def generatePossibleJoins(self):

    # Function is *limited to at most 4 joins*
    joins = {1 : [], 2 : [], 3: [], 4: []}
    joins[1] = list(self.tables.keys())
    # 2 joins
    for key in self.relations.keys():
      joins[2].append(list(key))
    # 3 joins
    for t in list(self.tables.keys()):
      for i,j in enumerate(joins[2]):
        if not t in j:
          # Check if relation exists between table under investigation
          # and other tables in join order
          for r in joins[2][i+1:]:
            if (t==r[0] and r[1] in j) or (t==r[1] and r[0] in j):
              newList = j.copy()
              newList.append(t)
              joins[3].append(newList)
    # 4 joins
    for t in list(self.tables.keys()):
      for i,j in enumerate(joins[3]):
        if not t in j:
          for r in joins[2]:
            if (t==r[0] and r[1] in j) or (t==r[1] and r[0] in j):
              newList = j.copy()
              newList.append(t)
              newList.sort()
              # Avoid double-adding of same relation
              if not newList in joins[4]:
                joins[4].append(newList)
    joins[4].sort() 
    return joins
  
  # Check if this relation is valid for the two provided tables
  def _relationExists(self, relation, table1, table2):
    return (relation[0] == table1 and relation[1] == table2) or \
           (relation[0] == table2 and relation[1] == table1)

  # 
  def getRelation(self, table1, table2):
    for r in self.relations.keys():
      if self._relationExists(r, table1, table2):
        return self.relations[r]
    return None

  # Consolidate and document + descriptive names
  def generateSQL(self, query, selected_op):
    # if chosen op is not SELECT, then only one table is needed
    if selected_op != "SELECT":
      query = [query]
    join = ""
    for table in query:
      join += table + ", "
    where_str = " WHERE "
    # WHERE is common to all queries
    join = join[:-2] + where_str
    and_str = " AND "
    #sql = "EXPLAIN (ANALYZE, VERBOSE, FORMAT JSON) "
    sql = ""
    sql += selected_op + " "
    if selected_op == "SELECT":
      # If SELECT, go through table combinations and apply some number of 
      # relations randomly
      # Probability of applying relations increases as number of tables in
      # query does
      table_combs = combinations(query, 2)
      rels_applied = False
      for combination in table_combs:
        apply_rel = random.randint(1,len(query))
        if (apply_rel > 0):
          rel = self.getRelation(combination[0], combination[1])
          if not rel==None:
            rels_applied = True
            chosen_rel = random.choice(rel)[0]
            join += chosen_rel + and_str
      if not rels_applied:
        join = join[::-1].replace(where_str[::-1], "", 1)[::-1]
      join = join[::-1].replace(and_str[::-1], "", 1)[::-1] + ";"

      # # Choose to make it a COUNT op randomly
      # count = random.randint(0,1)
      # if count:
      #   sql+= "COUNT(*) FROM "+join
      # else:
      #   sql+= "* FROM "+join
      
      # select all the colums from the tables
      column_counter = 0
      num_joins = len(query)
      if num_joins == 1 or num_joins == 2:
        boundary = 20
      elif num_joins ==3:
        boundary = 15
      elif num_joins==4:
        boundary = 10

      boundary = 2

      #print(len(query), ' boundary ', boundary)

      for q in query:

        dict_entry = self.tables[q] 
        cols = dict_entry[0]
        #cols_with_names = [q + "." + s for s in cols]
        #cols_add = ", ".join(cols_with_names)

        for s in cols:
          col_with_name = q + "." + s
          column_counter+=1
          #print(column_counter, " ", col_with_name)
          if column_counter<=boundary:
            sql+= col_with_name + ", "
          else: break

        #sql+=cols_add + ", "
      
      sql = sql[:-2]
      sql+= " FROM " + join

    # If INSERT op, get columns for table and generate data based on dtype
    elif selected_op == "INSERT":
      dict_entry = self.tables[query[0]]
      cols = dict_entry[0]
      dtypes = dict_entry[1]
      cols_add = str(tuple(cols)).replace('\'','\"')
      sample_entries = [dtype_samples[field] for field in dtypes]
      dtype_add = str(tuple(sample_entries)).replace('\"','\'')
      suffix = cols_add + " VALUES" + dtype_add
      sql += "INTO " + join + suffix
    # If UPDATE op, determine valid choice of column (that can be easily parsed) and set it to new value 
    elif selected_op == "UPDATE":
      dict_entry = self.tables[query[0]]
      cols = dict_entry[0]
      dtypes = dict_entry[1]
      valid_choices = []
      for col in cols:
        if ("id" in col.lower()) or (col == "year"):
          valid_choices.append(col)
      chosen_idx = random.randint(0, len(valid_choices)-1)
      chosen_col = valid_choices[chosen_idx]
      join = query[0] + " SET " 
      if "id" in chosen_col:
        update_val = chosen_col + "=99999"
        condition = chosen_col + "=" + str(random.randint(1, 20))
      elif chosen_col == "year":
        update_val = chosen_col + "=2099"
        condition = chosen_col + "=" + str(random.randint(1980, 2008))
      join += update_val + where_str + condition
      sql += join
    return sql
