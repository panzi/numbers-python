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
	uniq_solutions = set()

	lower = 0
	upper = numcnt
	while lower < upper:
		for b in xrange(lower,upper):
			for a in xrange(0,b):
				aexpr = exprs[a]
				bexpr = exprs[b]

				if all(not (x and y) for x, y in izip(aexpr.used,bexpr.used)):
					hasroom = not all(x or y for x, y in izip(aexpr.used,bexpr.used))
					for expr in make(aexpr,bexpr):
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
		lower = upper
		upper = len(exprs)

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
