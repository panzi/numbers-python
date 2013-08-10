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
		if left.value > right.value:
			left, right = right, left
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
		# don't create new objects if already normalized
		rt = type(self.right)
		lt = type(self.left)

		if lt is not Sub and rt not in (Add, Sub):
			if lt is Add:
				if self.left.right.value <= self.right.value:
					return self
			else:
				return self

		left_adds,  left_subs  = build_lists(self.left,Add,Sub)
		right_adds, right_subs = build_lists(self.right,Add,Sub)

		adds = merge(left_adds,right_adds)
		subs = merge(left_subs,right_subs)

		node = adds[0]
		for right in adds[1:]:
			node = Add(node,right)
		for right in subs:
			node = Sub(node,right)
		return node

	precedence = property(lambda self: 0)

def merge(left,right):
	lst = []
	i = len(left)  - 1
	j = len(right) - 1

	while i >= 0 and j >= 0:
		x = left[i]
		y = right[j]
		if x.value <= y.value:
			lst.append(x)
			i -= 1
		else:
			lst.append(y)
			j -= 1

	while i >= 0:
		lst.append(left[i])
		i -= 1
		
	while j >= 0:
		lst.append(right[j])
		j -= 1

	return lst
	

def build_lists(node,X,Y):
	xs = []
	ys = []
	while True:
		t = type(node)
		if t is X:
			xs.append(node.right)
			node = node.left
		elif t is Y:
			ys.append(node.right)
			node = node.left
		else:
			break
	xs.append(node)
	return xs, ys

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
	
	def normalize(self):
		# don't create new objects if already normalized
		rt = type(self.right)

		if rt not in (Add, Sub):
			if type(self.left) is Sub:
				if self.left.right.value <= self.right.value:
					return self
			else:
				return self

		left_adds,  left_subs  = build_lists(self.left,Add,Sub)
		right_subs, right_adds = build_lists(self.right,Add,Sub)

		adds = merge(left_adds,right_adds)
		subs = merge(left_subs,right_subs)

		node = adds[0]
		for right in adds[1:]:
			node = Add(node,right)
		for right in subs:
			node = Sub(node,right)
		return node
	
	precedence = property(lambda self: 1)
		
class Mul(BinExpr):
	__slots__ = ()
	def __init__(self,left,right):
		if left.value > right.value:
			left, right = right, left
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
		# don't create new objects if already normalized
		rt = type(self.right)
		lt = type(self.left)

		if lt is not Div and rt not in (Mul, Div):
			if lt is Mul:
				if self.left.right.value <= self.right.value:
					return self
			else:
				return self

		left_muls,  left_divs  = build_lists(self.left,Mul,Div)
		right_muls, right_divs = build_lists(self.right,Mul,Div)

		muls = merge(left_muls,right_muls)
		divs = merge(left_divs,right_divs)

		node = muls[0]
		for right in muls[1:]:
			node = Mul(node,right)
		for right in divs:
			node = Div(node,right)
		return node

	precedence = property(lambda self: 3)

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

	def normalize(self):
		# don't create new objects if already normalized
		rt = type(self.right)

		if rt not in (Mul, Div):
			if type(self.left) is Div:
				if self.left.right.value <= self.right.value:
					return self
			else:
				return self

		left_muls,  left_divs  = build_lists(self.left,Mul,Div)
		right_divs, right_muls = build_lists(self.right,Mul,Div)

		muls = merge(left_muls,right_muls)
		divs = merge(left_divs,right_divs)

		node = muls[0]
		for right in muls[1:]:
			node = Mul(node,right)
		for right in divs:
			node = Div(node,right)
		return node

	def order(self):
		return (4, self.value)

	precedence = property(lambda self: 2)

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

	precedence = property(lambda self: 4)

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
	uniq_solutions = set()
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
							wrapped = NumericHashedExpr(expr)
							if wrapped not in uniq_solutions:
								uniq_solutions.add(wrapped)
								yield expr
		m = len(exprs)
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
	try:
		for i, solution in enumerate(solutions(target,numbers)):
			now = time()
			print "%3d [%4d / %4d secs]: %s" % (i+1, now - last, now - start, solution)
			last = now
	except KeyboardInterrupt:
		print
	print "%f seconds in total" % (time() - start)

if __name__ == '__main__':
	import sys
	main(sys.argv)
