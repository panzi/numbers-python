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

	def annot_str_under(self,annot_map,precedence):
		return '(%s)' % self.annot_str(annot_map)
#		if precedence > self.precedence:
#			return '(%s)' % self.annot_str(annot_map)
#		else:
#			return self.annot_str(annot_map)

	def normalize(self):
		return self	

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
		if type(self) is not type(other):
			return False

		return self.left == other.left and self.right == other.right
	
	def numeric_hash(self):
		return hash((self.__class__, self.left.numeric_hash(), self.right.numeric_hash()))
	
	def numeric_eq(self,other):
		if type(self) is not type(other):
			return False

		return self.left.numeric_eq(other.left) and self.right.numeric_eq(other.right)
	
	def clone(self):
		return self.__class__(self.left,self.right,self.value)
	
	def deep_clone(self):
		return self.__class__(self.left.clone(),self.right.clone(),self.value)

class Add(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		BinExpr.__init__(self,left,right,left.value + right.value)

	def __str__(self):
		p = self.precedence
		return '%s + %s' % (self.left.str_under(p), self.right.str_under(p))

	def annot_str(self,annot_map):
		p = self.precedence
		return '%s + %s' % (
			self.left.annot_str_under(annot_map,p),
			self.right.annot_str_under(annot_map,p))

	def order(self):
		return (1, self.value)
	
	def normalize(self):
		# TODO: incorporate Sub
		if type(self.right) is Add:
			stack = [self.left]
			node = self.right
			while type(node) is Add:
				stack.append(node.right)
				node = node.left
			stack.append(node)
			stack.sort(key=lambda node:node.value)
			left = stack[0]
			for right in stack[1:]:
				left = Add(left,right)
			return left
		return self

	precedence = property(lambda self: 0)

class Sub(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		BinExpr.__init__(self,left,right,left.value - right.value)

	def __str__(self):
		p = self.precedence
		return '%s - %s' % (self.left.str_under(p), self.right.str_under(p))

	def annot_str(self,annot_map):
		p = self.precedence
		return '%s - %s' % (
			self.left.annot_str_under(annot_map,p),
			self.right.annot_str_under(annot_map,p))

	def order(self):
		return (2, self.value)
	
	# TODO: normalize
	
	precedence = property(lambda self: 0)
		
class Mul(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		BinExpr.__init__(self,left,right,left.value * right.value)
		
	def __str__(self):
		p = self.precedence
		return '%s * %s' % (self.left.str_under(p), self.right.str_under(p))

	def annot_str(self,annot_map):
		p = self.precedence
		return '%s * %s' % (
			self.left.annot_str_under(annot_map,p),
			self.right.annot_str_under(annot_map,p))

	def order(self):
		return (3, self.value)
		
	def normalize(self):
		if type(self.right) is Mul:
			stack = [self.left]
			node = self.right
			while type(node) is Mul:
				stack.append(node.right)
				node = node.left
			stack.append(node)
			stack.sort(key=lambda node:node.value)
			left = stack[0]
			for right in stack[1:]:
				left = Add(left,right)
			return left
		return self

	precedence = property(lambda self: 2)

class Div(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		BinExpr.__init__(self,left,right,left.value // right.value)
	
	def __str__(self):
		p = self.precedence
		return '%s / %s' % (self.left.str_under(p), self.right.str_under(p))

	def annot_str(self,annot_map):
		p = self.precedence
		return '%s / %s' % (
			self.left.annot_str_under(annot_map,p),
			self.right.annot_str_under(annot_map,p))

	# TODO: normalize

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

	def annot_str(self,annot_map):
		return str(self.value) + ("'" * annot_map[self.index])

	def annot_str_under(self,annot_map,precedence):
		return self.annot_str(annot_map)

	def __hash__(self):
		return self.index

	def __eq__(self,other):
		if type(self) is not type(other):
			return False

		return self.index == other.index

	def numeric_hash(self):
		return self.value

	def numeric_eq(self,other):
		if type(self) is not type(other):
			return False

		return self.value == other.value

	def order(self):
		return (0, -self.index)
	
	def clone(self):
		return Val(self.value,self.index,len(self.used))
	
	deep_clone = clone

	precedence = property(lambda self: 3)

class NumericHashedExpr(object):
	__slots__ = 'expr','__hash'
	def __init__(self,expr):
		self.expr = expr
		self.__hash = expr.numeric_hash()
	
	def __hash__(self):
		return self.__hash

	def __eq__(self,other):
		return self.expr.numeric_eq(other.expr)

def solutions(target,numbers):
	numcnt = len(numbers)
	exprs  = [Val(num,i,numcnt) for i, num in enumerate(numbers)]

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
					expr = expr.normalize()
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

def old_make(a,b):
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

def make(a,b):
	# TODO: proper normalization of expressions
	yield Add(a,b)

	if a.value != 1 and b.value != 1:
		yield Mul(a,b)

	if a.value > b.value:
		yield Sub(a,b)

		if b.value != 1 and a.value % b.value == 0:
			yield Div(a,b)
	
	elif b.value > a.value:
		yield Sub(b,a)

		if a.value != 1 and b.value % a.value == 0:
			yield Div(b,a)

	elif b.value != 1:
		yield Div(a,b)

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

	number_counts = {}
	annot_map = [0] * len(numbers)
	for i, num in enumerate(numbers):
		number_count = number_counts.get(num,0)
		annot_map[i] = number_count
		number_counts[num] =  number_count + 1

	print 'target   = %r' % target
	print 'numbers  = %r' % (numbers,)
#	print 'solution = %s' % exact_solution(target, numbers)

	print "solutions:"
	start = last = time()
	uniq_solutions = set()
	solution_nr = 1
	for solution in solutions(target,numbers):
		wrapped = NumericHashedExpr(solution)
		if wrapped not in uniq_solutions:
			uniq_solutions.add(wrapped)
			now = time()
			print "%3d [%4d / %4d secs]: %s" % (solution_nr, now - last, now - start, solution) #solution.annot_str(annot_map))
			last = now
			solution_nr += 1
	print "%f seconds in total" % (time() - start)

if __name__ == '__main__':
	import sys
	main(sys.argv)
