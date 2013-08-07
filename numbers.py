#!/usr/bin/env python

class Expr(object):
	__slots__ = ()
	def str_under(self,precedence):
		return '(%s)' % str(self)
#		if precedence > self.precedence:
#			return '(%s)' % str(self)
#		else:
#			return str(self)

	def __hash__(self):
		return hash(str(self))
	
	def __cmp__(self,other):
		return cmp(str(self),str(other))

class BinExpr(Expr):
	__slots__ = 'left', 'right', 'value'
	def __init__(self,left,right,value):
		self.left  = left
		self.right = right
		self.value = value
	
	def used(self,used):
		self.left.used(used)
		self.right.used(used)

	def __hash__(self):
		return hash((self.__class__, self.left, self.right))

	def __eq__(self,other):
		if type(self) != type(other):
			return False

		return self.left == other.left and self.right == other.right

class Add(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		if left.value > right.value:
			left, right = right, left
		BinExpr.__init__(self,left,right,left.value + right.value)
	
	def __str__(self):
		p = self.precedence
		return '%s + %s' % (self.left.str_under(p), self.right.str_under(p))
	
	precedence = property(lambda self: 0)

class Sub(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		BinExpr.__init__(self,left,right,left.value - right.value)

	def __str__(self):
		p = self.precedence
		return '%s - %s' % (self.left.str_under(p), self.right.str_under(p))
	
	precedence = property(lambda self: 0)
		
class Mul(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		if left.value > right.value:
			left, right = right, left
		BinExpr.__init__(self,left,right,left.value * right.value)
		
	def __str__(self):
		p = self.precedence
		return '%s * %s' % (self.left.str_under(p), self.right.str_under(p))
	
	precedence = property(lambda self: 2)

class Div(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		BinExpr.__init__(self,left,right,left.value // right.value)
	
	def __str__(self):
		p = self.precedence
		return '%s / %s' % (self.left.str_under(p), self.right.str_under(p))

	precedence = property(lambda self: 1)

class Val(Expr):
	__slots__ = 'value',
	def __init__(self,value):
		self.value = value
	
	def __str__(self):
		return str(self.value)

	def used(self,used):
		used[self.value] = used.get(self.value,0) + 1
	
	def str_under(self,precedence):
		return str(self.value)
	
	def __hash__(self):
		return hash(self.value)

	def __eq__(self,other):
		if type(self) != type(other):
			return False

		return self.value == other.value

	precedence = property(lambda self: 3)

def solutions(target,numbers):
	uniq  = set(numbers)
	avail = dict((num,numbers.count(num)) for num in uniq)
	exprs = [Val(num) for num in sorted(uniq)]
	combs = [bounded_combinations(len(exprs))]

	for expr in exprs:
		if expr.value == target:
			yield expr

	n = len(exprs)
	for comb in combs:
		for a, b in comb:
			a = exprs[a]
			b = exprs[b]
			used = {}
			a.used(used)
			b.used(used)
			if all(avail[val] >= used[val] for val in used):
				notfull = not all(avail[val] == used.get(val,0) for val in avail)
				for expr in make(a,b):
					if expr not in uniq:
						uniq.add(expr)
						issolution = expr.value == target
						if notfull and not issolution:
							exprs.append(expr)
						if issolution:
							yield expr
		m = len(exprs)
		# TODO: speedup by somehow not generating combinations that use too many numbers
		combs.append(combinations_slice(n,m))
		n = m

#      1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20
#  1
#  2   1
#  3   2   4
#  4   3   6   9
#  5   5   8  12  16
#  6   7  11  15  20  25
#  7  10  14  19  24  30  36
#  8  13  18  23  29  35  42   .
#  9  17  22  28  34  41   .   .   .
# 10  21  27  33  40   .   .   .   .   .
# 11  26  32  39   .   .   .   .   .   .   .
# 12  31  38   .   .   .   .   .   .   .   .   .
# 13  37   .   .   .   .   .   .   .   .   .   .   .
# 14   .   .   .   .   .   .   .   .   .   .   .   .   .
# 15   .   .   .   .   .   .   .   .   .   .   .   .   .   .
# 16   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .
# 17   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .
# 18   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .
# 19   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .
# 20   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .

def combinations():
	"""
	all integers >= 0 combined, no combinations with self and no reverse combinations
	"""
	i = 0
	while True:
		a = 0
		b = i
		while b > a:
			yield a, b
			b -= 1
			a += 1
		i += 1

def bounded_combinations(n):
	"""
	integers >= 0 and < n combined, no combinations with self and no reverse combinations
	"""
	i = 0
	while i < n:
		a = 0
		b = i
		while b > a:
			yield a, b
			b -= 1
			a += 1
		i += 1
	
	i = 1
	while i < n:
		a = i
		b = n - 1
		while b > a:
			yield a, b
			b -= 1
			a += 1
		i += 1

def combinations_slice(lower,upper):
	"""
	integers >= lower and < upper combined, no combinations with self and no reverse combinations
	"""
	if lower >= upper:
		return

	i = lower
	while i < upper:
		a = 0
		b = i
		while b > a and b >= lower:
			yield a, b
			b -= 1
			a += 1
		i += 1
	
	i = 1
	while i < upper:
		a = i
		b = upper - 1
		while b > a and b >= lower:
			yield a, b
			b -= 1
			a += 1
		i += 1

def make(a,b):
	exprs = [Add(a,b), Mul(a,b)]

	if a.value > b.value:
		exprs.append(Sub(a,b))
	
	elif b.value > a.value:
		exprs.append(Sub(b,a))

	if a.value % b.value == 0:
		exprs.append(Div(a,b))
		
	if b.value % a.value == 0:
		exprs.append(Div(b,a))
	
	return exprs

def solution(target, numbers):
	try:
		return solutions(target, numbers).next()
	except StopIteration:
		return None

def main(args):
	if len(args) < 3:
		raise ValueError("not enough arguments")
	
	target  = int(args[1],10)
	numbers = [int(arg,10) for arg in args[2:]]
	numbers.sort()

	if target <= 0:
		raise ValueError("target has to be > 0")

	if any(num <= 0 for num in numbers):
		raise ValueError("numbers have to be > 0")

	print 'target   = %r' % target
	print 'numbers  = %r' % (numbers,)
#	print 'solution = %s' % exact_solution(target, numbers)

	print "solutions:"
	for i, solution in enumerate(solutions(target,numbers)):
		print "%3d: %s" % (i+1, solution)

if __name__ == '__main__':
	import sys
	main(sys.argv)
