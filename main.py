import csv
from math import ceil

numMul = 0
numAdd = 0

def main():
  global numMul
  global numAdd
  # Read csv file
  with open("input.csv") as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    for row in csvreader:
      numMul = 0
      numAdd = 0
      A, B = row
      F, mulTime = mul(A, B, 0)
      print(f"<---------->"
            f"\nBinary: {A} * {B} = {F}"
            f"\nHex: {hex(int(A, 2))} * {hex(int(B, 2))} = {hex(int(F, 2))}"
            f"\nTime: {mulTime + int(ceil(numMul/4) * 21)}t"
            f"\nn: {len(A)}"
            f"\nMultiplications: {numMul}"
            f"\nAdditions: {numAdd}")

'''
Multiplies two n-bit unsigned binary numbers together
  using the wonders of recursion
Returns as [F, Time Elapsed]
'''
def mul(A: str, B: str, startTime: int):
  n = len(A)
  # End recursion at basic building block (4-bit numbers)
  if n <= 4:
    return [mul_4bit(A, B), startTime]
  # Zero extend numbers until they can be divided into 2 parts
  while len(A) % 2 != 0:
    A = '0' + A
    B = '0' + B
  # m will be used as temporary length
  m = len(A)

  # A = ab
  # B = cd
  # Generate ac, ad, bc, bd terms recursively and in parallel
  # Since 4-bit multiplications are tracked elsewhere, the additional time taken is 
  #   the time that one multiplication branch takes to complete, that branch being
  #   the last to use the 4-bit multiplication units.
  a = A[:int(m/2)]
  b = A[int(m/2):]
  c = B[:int(m/2)]
  d = B[int(m/2):]
  (ac, time) = mul(a, c, startTime)
  ad = mul(a, d, time)[0]
  bc = mul(b, c, time)[0]
  bd = mul(b, d, time)[0]

  # F = ac<<n + (ad + bc)<<n/2 + bd
  # Essentially just add ad and bc to the middle of acbd
  (f_temp, time) = add(ac+bd, ad, time)
  (F, time) = add(f_temp, bc, time)

  return [F[-2*n:], time]

'''
Adds numbers of lengths n and n/2,
  with the small number added to the middle of the larger,
  where n is the number of bits in the larger number
Time: 6t + 2((n/4)-1)t
Return as [large + small<<n/2, Finish Time]
'''
def add(large: str, small: str, startTime: int):
  global numAdd
  numAdd += 1
  n = len(large)
  # Check that sizes are correct
  if n/2 != len(small):
    print("Error: Adding size mismatch")
  
  # Zero extend large to have a length multiple of 4
  while len(large) % 4 != 0:
    large = '0' + large
  # Zero extend small to have same length as the section of large it's being added to
  while len(small) < len(large) - n/4:
    small = '0' + small

  # Add small in middle of large
  (f, fTime) = add_start(large[:-(int(n/4))], small)
  return [(f + large[-(int(n/4)):])[-n:], startTime + fTime]
  
'''
Adds two 4-bit numbers with a CLA1 to speed up this addition
  and a CLA2 to speed up carry out.
Time:
  t0 equates to when A and B are passed in
  Carry out and sum in 6t
Return value as [F, Calculation Time]
'''
def add_start(A: str, B: str):
  # Zero Extend A and B such that 4-bit addition blocks will always work
  while len(A) % 4 != 0:
    A = '0' + A
    B = '0' + B
  # t1
  # Generate Q's and G's in parallel (all in 1t)
  Q = []
  G = []
  # Reverse order so that G[0] = G0
  for bit1, bit2 in zip(reversed(A[-4:]), reversed(B[-4:])):
    Q += [bin_or(bit1, bit2)]
    G += [bin_and(bit1, bit2)]

  # Determine Carries (All happen simultaneously)
  C = ['','','','','']
  # Carry 0 is always 0
  C[0] = '0'
  # Carry 1 = G0 (Generated in 1t)
  # t2
  C[1] = G[0]
  # Carry 2 = G1 + Q1G0 (Generated in 2t)
  # t2
  Q1G0 = bin_and(Q[1], G[0])
  # t3
  C[2] = bin_or(G[1], Q1G0)
  # Carry 3 = G2 + Q2G1 + Q2Q1G0 (Generated in 3t)
  # t2
  Q2G1 = bin_and(Q[2], G[1])
  Q2Q1 = bin_and(Q[2], Q[1])
  # t3
  G2_Q2G1 = bin_or(G[2], Q2G1)
  Q2Q1G0 = bin_and(Q2Q1, G[0])
  # t4
  C[3] = bin_or(G2_Q2G1, Q2Q1G0)
  # After t4, the sum and carry out can start to be determined
  # Determine Carry Out during t5 and t6
  # Cout = G3 + Q3C3
  # t5
  Q3C3 = bin_and(Q[3], C[3])
  # t6
  C[4] = bin_or(G[3], Q3C3)
  # At t6, the carry can be propagated to the next selection mux

  # Simultaneously determine sum bits F[3..0]
  # All iterations in this loop happen simultaneously
  F = ''
  for A_bit, B_bit, C_bit in zip(reversed(A[-4:]), reversed(B[-4:]), C):
    # The first operation happens during t1 and t2
    F_temp = bin_xor(A_bit, B_bit)
    # The second operation happens after carry calculations,
    # during t5 and t6
    F = bin_xor(F_temp, C_bit) + F
  
  # Add rest of the bits
  (temp_f, fTime) = add_recursive(A[:-4], B[:-4], C[4], 6)

  # Return value as [F, Time F Completed]
  return [temp_f + F, fTime]

'''
Recursive 4-bit addition using CLA1 and Carry Select
Time:
  The sequential elements of this function start when the carry is passed in.
    This either equates to the end of t6 in the add_start function
    or when the previous add_recursive selects its carry and F. 
  All CLA1 blocks for all add_CLA1 calls will finish potential carries and sums
    by t6 in the add_start function.
  Next, a cascade of 2-bit MUXes will select carries and Fs, taking 2t per cascade.
  Total time from when A & B are known: 8t+
Return value as [F, Time F Completed]  
'''
def add_recursive(A: str, B: str, Cin: str, Cin_time: int):
  # End recursion if there are no more bits to add
  if len(A) == 0:
    return ['', Cin_time]
  else:
    # Add next 4 bits and call function again
    
    # The addition of each section here is done between the add_start's t1 and t6, inclusive.
    # This is possible due to the carry select method.

    # t1
    # Generate Q's and G's in parallel (all in 1t)
    Q = []
    G = []
    # Reverse order so that G[0] = G0
    for bit1, bit2 in zip(reversed(A[-4:]), reversed(B[-4:])):
      Q += [bin_or(bit1, bit2)]
      G += [bin_and(bit1, bit2)]
    
    # Determine Carries for both potential values of Cin
    # Both sections occur simultaneously, and finish by 4t from add_start's start

    # Determine Carries and Sum for Cin = 0
    # Carry out does not need to be determined ahead of time
    C0 = ['', '', '', '', '']
    # Carry 0 is always 0
    C0[0] = '0'
    # Carry 1 = G0 (Generated in 0t)
    # t1
    C0[1] = G[0]
    # Carry 2 = G1 + Q1G0 (Generated in 2t)
    # t2
    Q1G0 = bin_and(Q[1], G[0])
    # t3
    C0[2] = bin_or(G[1], Q1G0)
    # Carry 3 = G2 + Q2G1 + Q2Q1G0 (Generated in 3t)
    # t2
    Q2G1 = bin_and(Q[2], G[1])
    Q2Q1 = bin_and(Q[2], Q[1])
    # t3
    G2_Q2G1 = bin_or(G[2], Q2G1)
    Q2Q1G0 = bin_and(Q2Q1, G[0])
    # t4
    C0[3] = bin_or(G2_Q2G1, Q2Q1G0)
    # After t4, the sum can start to be determined 
    # t5-t6
    # Simultaneously determine sum bits F[3..0] and carry out
    # All iterations in this loop happen simultaneously
    F0 = ''
    for A_bit, B_bit, C_bit in zip(reversed(A[-4:]), reversed(B[-4:]), C0):
      # The first operation happens during t1 and t2
      F_temp = bin_xor(A_bit, B_bit)
      # The second operation happens after carry calculations,
      # during t5 and t6
      F0 = bin_xor(F_temp, C_bit) + F0
    # Determine Carry Out during t5 and t6
    # Cout = G3 + Q3C3
    # t5
    Q3C3 = bin_and(Q[3], C0[3])
    # t6
    C0[4] = bin_or(G[3], Q3C3)

    # Determine Carries for Cin = 1
    # Carry out does not need to be determined ahead of time
    C1 = ['', '', '', '', '']
    # Carry 0 is always 1
    C1[0] = '1'
    # Carry 1 = G0 + Q0 (Generated in 1t)
    # t2
    C1[1] = bin_or(G[0], Q[0])
    # Carry 2 = G1 + Q1G0 + Q1Q0 (Generated in 3t)
    # t2
    Q1G0 = bin_and(Q[1], G[0])
    Q1Q0 = bin_and(Q[1], Q[0])
    # t3
    G1_Q1Q0 = bin_or(G[1], Q1G0)
    # t4
    C1[2] = bin_or(G1_Q1Q0, Q1Q0)
    # Carry 3 = G2 + Q2G1 + Q2Q1G0 + Q2Q1Q0 (Generated in 3t)
    # t2
    Q2G1 = bin_and(Q[2], G[1])
    Q2Q1 = bin_and(Q[2], Q[1])
    G0_Q0 = bin_or(G[0], Q[0])
    # t3
    G2_Q2G1 = bin_or(G[2], Q2G1)
    Q2Q1pG0_Q0 = bin_and(Q2Q1, G0_Q0)
    # t4
    C1[3] = bin_or(G2_Q2G1, Q2Q1pG0_Q0)
    # After t4, the sum can start to be determined 
    # t5-t6
    # Simultaneously determine sum bits F[3..0] and carry out
    # All iterations in this loop happen simultaneously
    F1 = ''
    for A_bit, B_bit, C_bit in zip(reversed(A[-4:]), reversed(B[-4:]), C1):
      # The first operation happens during t1 and t2
      F_temp = bin_xor(A_bit, B_bit)
      # The second operation happens after carry calculations,
      # during t5 and t6
      F1 = bin_xor(F_temp, C_bit) + F1
    # Determine Carry Out during t5 and t6
    # Cout = G3 + Q3C3
    # t5
    Q3C3 = bin_and(Q[3], C1[3])
    # t6
    C1[4] = bin_or(G[3], Q3C3)
    
    # At this point, the program waits for the carry in to be known
    # The carry is known before the first call finishes determining F's and Cout (at 5t)
    # Otherwise, it happens after the the potential F's and Cout are determined
    # Multiplexing takes 2t in total
    Cout = mux(C0[4], C1[4], Cin)
    F = mux(F0, F1, Cin)

    # Determine finishing time
    Out_time = Cin_time + 2

    # Add next 4 bits (if they exist)
    (temp_f, Out_time) = add_recursive(A[:-4], B[:-4], Cout, Out_time)

    return [temp_f + F, Out_time]


'''
<---HELPER FUNCTIONS--->
These functions are given as basic building blocks, and are thus not described at a gate level.
'''

'''
Multiplies two 4-bit numbers.
Numbers are inputted as strings containing 4-bit binary numbers
Time: 21t
'''
def mul_4bit(int1: str, int2: str):
  # Keep track of number of mul_4bit calls for time calculations
  global numMul
  numMul += 1
  # Convert to integers
  multiplier = int(int1, 2)
  multiplicand = int(int2, 2)
  # Check size of integer
  if multiplier > 15 or multiplicand > 15:
    print("Error: Large number put into mul_4bit")
  # Multiply numbers
  output = bin(multiplier * multiplicand)[2:]
  # Zero extend to reach desired length
  while(len(output) < len(int1) * 2):
    output = '0' + output
  return output

'''
Binary Gate function definitions
'''
def bin_or(bit1: str, bit2: str):
  return '1' if bit1 == '1' or bit2 == '1' else '0'

def bin_and(bit1: str, bit2: str):
  return '1' if bit1 == '1' and bit2 == '1' else '0'

def bin_not(bit: str):
  return '1' if bit == '0' else '0'

def bin_xor(bit1: str, bit2: str):
  return '1' if '1' in [bit1, bit2] and '0' in [bit1, bit2] else '0'

'''
Multiplexes two inputs based on the third input bit, C
'''
def mux(A: str, B: str, C: str):
  return A if C == '0' else B

main()