import numpy as np
np.seterr(all="raise")

import subprocess
import numpy as np
import random

import os
import shutil

def subprocess_cmd(command):
    process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True, cwd=r'../VHDL/individuals')
    proc_stdout = process.communicate()[0].strip()
    return proc_stdout.decode('utf-8')

def eval_vhdl(phenotype):
    r = random.randint(0,10**10)
    vhdl = open(r'../VHDL/individuals/ind' + str(r) + '.vhdl','w+')
    tb = open(r'../VHDL/individuals/tb' + str(r) + '.vhdl','w+')
    
    vhdl.write("""library ieee; 
use ieee.std_logic_textio.all;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity ind""" +  str(r) +  """ is 
port(a: in  STD_LOGIC_VECTOR (1 downto 0); 
     b: in  STD_LOGIC_VECTOR (1 downto 0); 
     o: out STD_LOGIC_VECTOR (3 downto 0)); 
end ind""" +  str(r) +  """;

""")
    tb.write("""library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb""" +  str(r) +  """ is
end tb""" +  str(r) +  """;

architecture dataflow of tb""" +  str(r) +  """ is
    signal aa: STD_LOGIC_VECTOR (1 downto 0); 
    signal bb: STD_LOGIC_VECTOR (1 downto 0); 
""")
    n = 0
    phenotype = phenotype.replace('dataflow', 'dataflow' + str(r) + str(n))
    phenotype = phenotype.replace('ind', 'ind' + str(r))
    phenotype = phenotype.replace('==', '<=')
#    phenotype = phenotype.replace('   ', '')
    vhdl.write(phenotype + "\n\n")
    tb.write("    signal o" + str(r)  + str(n) + ": STD_LOGIC_VECTOR (3 downto 0);\n")
    n += 1
            
    tb.write("\nbegin\n")
    for i in range(n):
        tb.write("ind" + str(r) + str(i) + ": entity work.ind" + str(r) + "(dataflow" + str(r) + str(i) + ") port map (a => aa, b => bb, o => o" + str(r) + str(i) + ");\n")
    tb.write("""process 
variable count: std_logic_vector(3 downto 0);
begin 

for idx in 0 to 15 loop
count := std_logic_vector(to_unsigned(idx,4));
	
aa(1) <= count(0);
aa(0) <= count(1);
bb(1) <= count(2);
bb(0) <= count(3);

wait for 1 ns; 
report "'" """)

    for i in range(n):
        tb.write("& to_hstring(o" + str(r) + str(i) + ") & \"'\" ")
    tb.write(";\n\n end loop; wait; end process; end dataflow;")
    
    vhdl.close()
    tb.close()
    
    result = subprocess_cmd("ghdl -a --std=08 --work=" + str(r) + " ind" + str(r) + ".vhdl tb" + str(r) + ".vhdl ; ghdl -e --std=08 --work=" + str(r) + " tb" + str(r) + " ; ghdl -r --std=08  --work=" + str(r) + " tb"  + str(r))
    
    result_lines = result.replace("\r", "") #each line report the results from all individuals using one sample
    results_splitted = result_lines.split("'")
    
    for i in range(16):
        del results_splitted[i] #list with all results
    
    yhat = results_splitted[0:len(results_splitted)-1]
    for j in range(len(yhat)):
        yhat[j] = int(yhat[j],16)
    assert np.isrealobj(yhat)
           
    os.remove(r'../VHDL/individuals/tb' + str(r) + '.vhdl')
    os.remove(r'../VHDL/individuals/ind' + str(r) + '.vhdl')
    os.remove(r'../VHDL/individuals//' + str(r) + '-obj08.cf')

    return yhat