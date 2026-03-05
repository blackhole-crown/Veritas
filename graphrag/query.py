import subprocess

def get_query_coe(news):
#     Q = f"Now you should classify the following NEWS. Please provide a **chain of evidence** as above and give a clear judgment result (TRUE or FALSE, wrapped in **).\n\
# NEWS: **{news}**"

    Q = f"You are now required to classify the following NEWS. Please present a **chain of evidence** as outlined above, and provide a definitive judgment result (TRUE or FALSE, wrapped in **).\n\
NEWS: **{news}**"
    
    return Q

def get_answer(output_raw, query_methond):
    if query_methond == "local":
        return output_raw[output_raw.find('Local Search Response:') + len('Local Search Response:'):].strip()
    elif query_methond == "global":
        return output_raw[output_raw.find('Global Search Response:') + len('Global Search Response:'):].strip()
    else:
        raise Exception("Error search method!")

query_methond = 'global'
root_dir = 'sample'
claim = 'You have areas of Pennsylvania that are barely affected and [the governor wants] to keep them closed.'
# claim_date = '2020-03-31'

print(get_query_coe(claim))
print()
result = subprocess.run([
    'graphrag', 'query', 
    '--root', root_dir,
    '--method', query_methond,
    '--query', get_query_coe(claim)
], 
    capture_output=True, text=True)


with open('output.txt', 'w', encoding='utf-8') as file:
    file.write(get_answer(result.stdout, query_methond))

with open('log.txt', 'w', encoding='utf-8') as file:
    file.write(str(result))
# if os.path.exists(root_dir + '/output'):
#     shutil.rmtree(root_dir + '/output')

