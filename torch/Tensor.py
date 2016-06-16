
class RealTensor(RealTensorBase):
    def __str__(self):
        return "RealTensor"

    def __repr__(self):
        return str(self)

    def new(self, *args, **kwargs):
        return self.__class__(*args, **kwargs)

    def type(self, t):
        current = "torch." + self.__class__.__name__
        if not t:
            return current
        if t == current:
            return self
        _, _, typename = t.partition('.')
        # TODO: this is ugly
        assert hasattr(sys.modules['torch'], typename)
        return getattr(sys.modules['torch'], typename)(self.size()).copy(self)

    def typeAs(self, t):
        return self.type(t.type())

    def double(self):
        return self.type('torch.DoubleTensor')

    def float(self):
        return self.type('torch.FloatTensor')

    def long(self):
        return self.type('torch.LongTensor')

    def int(self):
        return self.type('torch.IntTensor')

    def short(self):
        return self.type('torch.ShortTensor')

    def char(self):
        return self.type('torch.CharTensor')

    def byte(self):
        return self.type('torch.ByteTensor')

    def __str__(self):
        return _printing.printTensor(self)

    def __iter__(self):
        return iter(map(lambda i: self.select(0, i), range(self.size(0))))

    def split(self, split_size, dim=0):
        result = []
        dim_size = self.size(dim)
        num_splits = math.ceil(dim_size / split_size)
        last_split_size = split_size * num_splits - dim_size or split_size
        def get_split_size(i):
            return split_size if i < num_splits-1 else last_split_size
        return [self.narrow(dim, i*split_size, get_split_size(i)) for i
                in range(0, num_splits)]

    def chunk(self, n_chunks, dim=0):
        split_size = math.ceil(tensor.size(dim)/n_chunks)
        return torch.split(tensor, split_size, dim)

    def tolist(self):
        dim = self.dim()
        if dim == 1:
            return [v for v in self]
        elif dim > 0:
            return [subt.tolist() for subt in self]
        return []

    def view(self, src, *args):
        assert isTensor(src)
        if len(args) == 1 and isStorage(args[0]):
            sizes = args[0]
        else:
            sizes = LongStorage(args)
        sizes = infer_sizes(sizes, src.nElement())

        assert src.isContiguous(), "expecting a contiguous tensor"
        self.set(src.storage(), src.storageOffset(), sizes)
        return self

    def viewAs(self, src, template):
        if not isTensor(src) and isLongStorage(template):
            raise ValueError('viewAs is expecting a Tensor and LongStorage')
        return self.view(src, template.size())

    def permute(self, *args):
        perm = list(args)
        tensor = self
        n_dims = tensor.dim()
        assert len(perm) == n_dims, 'Invalid permutation'
        for i, p in enumerate(perm):
            if p != i and p != -1:
                j = i
                while True:
                    assert 0 <= perm[j] and perm[j] < n_dims, 'Invalid permutation'
                    tensor = tensor.transpose(j, perm[j])
                    perm[j], j = -1, perm[j]
                    if perm[j] == i:
                        break
                perm[j] = -1
        return tensor

    def expand(self, src, *args):
        if not isTensor(src):
            if isStorage(src) and len(args) == 0:
                sizes = src
            else:
                # TODO: concat iters
                sizes = LongStorage([src] + list(args))
            src = self
            result = self.new()
        else:
            sizes = LongStorage(args)
            result = self

        src_dim = src.dim()
        src_stride = src.stride()
        src_size = src.size()

        if sizes.size() != src_dim:
            raise ValueError('the number of dimensions provided must equal tensor.dim()')

        # create a new geometry for tensor:
        for i, size in enumerate(src_size):
            if size == 1:
                src_size[i] = sizes[i]
                src_stride[i] = 0
            elif size != sizes[i]:
                ValueError('incorrect size: only supporting singleton expansion (size=1)')

        result.set(src.storage(), src.storageOffset(),
                                src_size, src_stride)
        return result