#Ronan McMullen - 0451657

import operator
import os.path
import random
#from PIL.Image import NONE
import re
import sys
import numpy as np
#import matplotlib.pyplot as plt


from deap import base, gp
from deap import creator
from deap import tools
from deap import algorithms

from supervised_learning_vhdl import eval_vhdl

class Phenotype(object):
    """
    A GE phenotype.
    """

    def __init__(self):
        """
        
        """

        self.phenome = None
        self.invalid = False


INDIVIDUAL_LENGTH = 2000# length of bit string to be optimized

GRAMMAR = "2bit_multiplierB.bnf"

# Genetic Algorithm constants:
POPULATION_SIZE = 500
P_CROSSOVER = 0.8 # probability for crossover
P_MUTATION = 0.01   # probability for mutating an individual
MAX_GENERATIONS = 50
HALL_OF_FAME_SIZE = 5
N_RUNS = 1

# Initialize 2-bits Multiplier problem output vector
# The input vector is defined by the testbench (VHDL)

y = [0, 0, 0, 0, 0, 1, 2, 3, 0, 2, 4, 6, 0, 3, 6, 9]


# set the random seed:
RANDOM_SEED = None #random.randint(1, 1000)
#print(RANDOM_SEED)
random.seed(RANDOM_SEED)   
 
def g2p_map (individual):

    """This function accepts a variable length bit string genome. It parses the genome in 8-bit codons.
    Each codon is converted to its corresponding decimal value. This decimal value is modded (%) by the number of choices
    available in the current non-terminal and the resulting value is used to determine which choice is selected."""

    tree_depth = 0

    choices = list() # genome
    codon = ""
    i=0
    for bit in individual:
        codon += str(bit)
        i+=1
        if i % 8 == 0:
            n = parse_codon(codon) #n = int; codon = 8 bits
            choices.append(n)
            codon = ""

    phenome = prod_rule_dict['S'][0]
    print_out = False
    wrapping = 0
    i=0
#    max_depth = 20#6
    while(True):

        non_terminal = re.search("<.*?>", phenome)

        if(non_terminal is not None and i < len(choices)):
#            if tree_depth < max_depth:
            component = non_terminal.group(0)
#            else:
#                component = "<var>"
#                phenome = phenome.replace("<sub-expr>", "<var>")

#            if component == "<push_tree>":
#                tree_depth += 1
            
            rule = prod_rule_dict[component]
            
            phenome = phenome.replace(component, rule[choices[i] % len(rule)], 1)

            #the -P- is the symbol input in place of push_tree.
#            phenome = phenome.replace("-P-", "")
            if(print_out):
#                print("Tree depth:", tree_depth)
                print("Phenome length:", len(phenome))
                print("Component:", component)
                print("Rule:", rule, ", len(rule):", len(rule))
                print("Codon to decimal element",  i, "=", choices[i])
                print(choices[i], "%", len(rule), ":", choices[i] % len(rule))
                print("Choice:", rule[choices[i] % len(rule)] )
                print("Phenome =", phenome)
                print(" ")
        elif(non_terminal is not None and i >= len(choices)):
            invalid = True #The phenotype was not completed
            break
        else:
            invalid = False
            break
        i+=1
   
    return phenome, invalid
    
def bnf_parse (filename):
    """this function will parse the specified bnf file
    and add it to a usable data structure that can be accessed
    by the g2p_map function.
    The bnf grammar is kept in a seperate accessible .pybnf file"""

    #TODO Enure leading and trailing whitespace is removed from file before parsing.
    if not os.path.isfile(filename):
        print('File', filename, 'does not exist.')
    else:
        with open(filename) as f:
            grammar = f.read().splitlines()

        for g in grammar:
            #g = g.replace(" ", "")
            rule = g.split("::=")
            rule[0] = rule[0].replace(" ", "")
            title = rule[0]
            components = rule[1].split("|")    
            prod_rule_dict[title] = components
         
def parse_codon (codon):
    """this helper function parses an 8bit binary number
    and returns its decimal representation"""

    c = list(codon)
    n = 0
    i = 7

    for bit in c:
        if bit == "1":
            n = n + pow(2,i)
        i -= 1

    return n

def fitness_eval (individual):#, points)

    phenome = Phenotype()

    phenome.phenotype, phenome.invalid = g2p_map(individual)
    # Transform the tree expression in a callable function
 #   func = toolbox.compile(expr=phenome)

    if phenome.invalid == True:
        return 1,
    
    yhat = eval_vhdl(phenome.phenotype)
    
    compare = np.equal(y,yhat)
    
    fitness = 1 - np.mean(compare)

    return fitness,


toolbox = base.Toolbox()

production_rules = []
prod_rule_dict = {}

# create an operator that randomly returns 0 or 1:
toolbox.register("zeroOrOne", random.randint, 0, 1)

#toolbox.register("compile", gp.compile, pset=pset)

# define a single objective, maximizing fitness strategy:
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

# create the Individual class based on list:
creator.create("Individual", list, fitness=creator.FitnessMin)
#creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin)

# create the individual operator to fill up an Individual instance:
toolbox.register("individualCreator", tools.initRepeat, creator.Individual, toolbox.zeroOrOne, INDIVIDUAL_LENGTH)

# create the population operator to generate a list of individuals:
toolbox.register("populationCreator", tools.initRepeat, list, toolbox.individualCreator)

toolbox.register("evaluate", fitness_eval)#, points=[x for x in np.linspace(0, 10, 100)])

# genetic operators:
#toolbox.register("select", tools.selTournament, tournsize=10)
toolbox.register("select", tools.selLexicase)

# Single-point crossover:
toolbox.register("mate", tools.cxOnePoint)


# Flip-bit mutation:
# indpb: Independent probability for each attribute to be flipped
toolbox.register("mutate", tools.mutFlipBit, indpb=P_MUTATION)


def main():

    bnf_parse("./grammars/"+GRAMMAR)

    global N_RUNS

    avg_list = []
    min_list = []
    

    for _ in range(0, N_RUNS):
        
        # create initial population (generation 0):
        population = toolbox.populationCreator(n=POPULATION_SIZE)

        # define the hall-of-fame object:
        hof = tools.HallOfFame(HALL_OF_FAME_SIZE)

        # prepare the statistics object:
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)


        # perform the Genetic Algorithm flow:
        population, logbook = algorithms.eaSimple(population, toolbox, cxpb=P_CROSSOVER, mutpb=P_MUTATION,
                                                  ngen=MAX_GENERATIONS,
                                                  stats=stats, halloffame=hof, verbose=True)

        # Genetic Algorithm is done - extract statistics:
        max_fitness_values, mean_fitness_values = logbook.select("min", "avg")
       
        # Genetic Algorithm is done with this run - extract statistics:
        max_fitness_values, mean_fitness_values= logbook.select("min", "avg")
        
        # Save statistics for this run:
        avg_list.append(mean_fitness_values)
        min_list.append(max_fitness_values)


    best = g2p_map(hof.items[0])

    for i in range(5):
        print(g2p_map(hof.items[i]))

if __name__ == "__main__":
    main()  