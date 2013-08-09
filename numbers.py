#!/usr/bin/env python

from itertools import izip

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
	__slots__ = 'left', 'right', 'value', 'used'
	def __init__(self,left,right,value):
		self.left  = left
		self.right = right
		self.value = value
		self.used  = [l or r for l, r in izip(left.used,right.used)]

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

	def order(self):
		return (1, self.value)

	precedence = property(lambda self: 0)

class Sub(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		BinExpr.__init__(self,left,right,left.value - right.value)

	def __str__(self):
		p = self.precedence
		return '%s - %s' % (self.left.str_under(p), self.right.str_under(p))

	def order(self):
		return (2, self.value)
	
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

	def order(self):
		return (3, self.value)

	precedence = property(lambda self: 2)

class Div(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		BinExpr.__init__(self,left,right,left.value // right.value)
	
	def __str__(self):
		p = self.precedence
		return '%s / %s' % (self.left.str_under(p), self.right.str_under(p))

	def order(self):
		return (4, self.value)

	precedence = property(lambda self: 1)

class Val(Expr):
	__slots__ = 'value','used','index'
	def __init__(self,value,index,numcnt):
		self.value = value
		self.index = index
		self.used  = [False] * numcnt
		self.used[index] = True
	
	def __str__(self):
		return str(self.value)

	def str_under(self,precedence):
		return str(self.value)
	
	def __hash__(self):
		return hash(self.index)

	def __eq__(self,other):
		if type(self) != type(other):
			return False

		return self.index == other.index

	def order(self):
		return (0, self.index)

	precedence = property(lambda self: 3)

def solutions(target,numbers):
	numcnt = len(numbers)
	exprs  = [Val(num,i,numcnt) for i, num in enumerate(sorted(numbers))]

	for expr in exprs:
		if expr.value == target:
			yield expr

	uniq = set(exprs)
	n = numcnt
	comb = bounded_combinations(len(exprs))
	while True:
		for a, b in comb:
			a = exprs[a]
			b = exprs[b]

			if all(not (x and y) for x, y in izip(a.used,b.used)):
				hasroom = not all(x or y for x, y in izip(a.used,b.used))
				for expr in make(a,b):
					if expr not in uniq:
						uniq.add(expr)
						issolution = expr.value == target
						if hasroom and not issolution:
							exprs.append(expr)
						if issolution:
							yield expr
		m = len(exprs)
		# TODO: speedup by somehow not generating combinations that use too many numbers
		if n < m:
			comb = combinations_slice(n,m)
			n = m
		else:
			break

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
	# bring commutative operations in normalized order
	# TODO: proper normalization of expressions
	if a.value > b.value:
		yield Add(a,b)

		if a.value != 1 and b.value != 1:
			yield Mul(a,b)

		yield Sub(a,b)

		if b.value != 1 and a.value % b.value == 0:
			yield Div(a,b)
	
	elif b.value > a.value:
		yield Sub(b,a)

		if a.value != 1 and b.value % a.value == 0:
			yield Div(b,a)

	elif a.order() > b.order():
		yield Add(a,b)

		if a.value != 1 and b.value != 1:
			yield Mul(a,b)

		if b.value != 1:
			yield Div(a,b)
	else:
		yield Add(b,a)

		if b.value != 1 and a.value != 1:
			yield Mul(b,a)

		if a.value != 1:
			yield Div(b,a)

def solution(target, numbers):
	try:
		return solutions(target, numbers).next()
	except StopIteration:
		return None

def main(args):
	from time import time

	if len(args) < 3:
		raise ValueError("not enough arguments")
	
	target  = int(args[1],10)
	numbers = [int(arg,10) for arg in args[2:]]
	numbers.sort()

	if target < 0:
		raise ValueError("target has to be >= 0")

	if any(num <= 0 for num in numbers):
		raise ValueError("numbers have to be > 0")

	print 'target   = %r' % target
	print 'numbers  = %r' % (numbers,)
#	print 'solution = %s' % exact_solution(target, numbers)

	print "solutions:"
	start = last = time()
	for i, solution in enumerate(solutions(target,numbers)):
		now = time()
		print "%3d [%4d / %4d secs]: %s" % (i+1, now - last, now - start, solution)
		last = now
	print "%f seconds in total" % (time() - start)

if __name__ == '__main__':
	import sys
	main(sys.argv)
