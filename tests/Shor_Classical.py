import random

def shor_classical(N):
    p = 1.0
    q = 1.0
    while p == 1 or q == 1 or p*q != N:
        r = -1
        a = 1
        while r%2 != 0 and a ** (r/2) != -1%N:
            a = random.randint(2, N-1)
            while gcd(a,N) != 1:
                a = random.randint(2, N-1)
            
            r = find_period(a, N)
            #print("Period", r)
        
        print("a", a, "r", r)
        
        #check if we will overflow
        if r != 1:
            p = modular_pow(a, r/2, N)
            print(p)
            p = p - 1

            q = modular_pow(a, r/2, N)
            q = q + 1
            print("p: ", p, "q: ", q)
        p = gcd(p,N)
        q = gcd(q,N)
    return p,q

#calculate the modular of a^r/2 mod N without overflowing with a^r/2
def modular_pow(base, exponent, modulus):
    result = 1      
    while exponent > 0:
        if (exponent%2 == 1):
            result = (result * base)% modulus 
        exponent = int(exponent) >> 1
        base = (base * base)%modulus
    return result
    
#find the period for some a, N
def find_period(a, N):
    val = a
    r = 1
    while val%N != 1:
        val *= a
        r += 1
    return r
    


#determine if a number is prime
def miller_rabin(n):
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    t = 10
    s = 0
    m = n - 1
    while m % 2 == 0:
        s += 1
        m /= 2
    for _ in range(t):
        a = random.randint(2, n-2)
        x = pow(a, int(m), n)
        if x == 1:
            continue
        j = 0
        while j < s and x != n-1:
            x = (x * x) % n
            j += 1
        if j >= s:
            return False
    return True

#calculate greatest common factor, used to check coprime
def gcd(a, b):
    if b > a:
        a, b = b, a
    while b > 0:
        a = a % b
        a, b = b, a
    return a

def main():
    N = [21, 35, 527,589,1271,8633,262417,282943,988027,113507707]
    for i in N:
        print(shor_classical(i))
    '''
    #testing success rate
    success = 0
    fail = 0
    for i in range(1000):
        try:
            shor_classical(N)
            success += 1
        except:
            fail+=1
    print(success)
    print(success/success+fail)
    '''

if __name__== '__main__':
    main()