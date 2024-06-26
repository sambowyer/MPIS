from .utils import *

class Moment:
    pass

class RawMoment(Moment):
    """
    Must be overwritten with self.f as a static method.
    """
    def __init__(self, f):
        self.f = f

    def from_samples(self, samples:tuple[Tensor], Ndim:Dim):
        return self.f(*samples).mean(Ndim)

    def from_marginals(self, samples:tuple[Tensor], weights:Tensor, all_platedims:dict[str, Dim]):
        assert isinstance(samples, tuple)
        assert isinstance(weights, Tensor)

        set_all_platedims = set(all_platedims.values())
        f = self.f(*samples)
        f_Kdims = set(generic_dims(f)).difference(set_all_platedims)
        w_Kdims = set(generic_dims(weights)).difference(set_all_platedims)
        assert f_Kdims.issubset(w_Kdims)
        tuple_w_Kdims = tuple(w_Kdims)
        assert 0 < len(tuple_w_Kdims)

        # The below 'detach' is a hack to avoid a bug in how pytorch deals with named tensors.  It should be removed when the bug is fixed.
        # The problem is that without the detach, the tensor f*weights is not instantiated, causing the sum to error with message "Aborted".
        # By detaching, we force the instantiation of the tensor, and the sum works fine. (Note that the choice of detatch is somewhat arbitrary.)
        # 
        # Potentially, we could replace the line instead by
        #   return t.sum(f*weights, tuple_w_Kdims)
        # but this needs to be tested.
        return (f*weights).detach().sum(tuple_w_Kdims) 

    def all_raw_moments(self):
        return [self.f]



class CompoundMoment(Moment):
    def __init__(self, combiner, raw_moments):
        self.combiner = combiner
        for rm in raw_moments:
            assert isinstance(rm, RawMoment)
        self.raw_moments = raw_moments

    def from_samples(self, samples:tuple[Tensor], Ndim):
        moments = [rm.from_samples(samples, Ndim) for rm in self.raw_moments]
        return self.combiner(*moments)

    def from_marginals(self, samples:tuple[Tensor], weights:Tensor, all_platedims:dict[str, Dim]):
        moments = [rm.from_marginals(samples, weights, all_platedims) for rm in self.raw_moments]
        return self.combiner(*moments)

    def all_raw_moments(self):
        return self.raw_moments

def var_from_raw_moment(rm:RawMoment):
    assert isinstance(rm, RawMoment)
    rm2 = RawMoment(lambda x: (rm.f(x))**2)
    return CompoundMoment(lambda Ex, Ex2: Ex2 - Ex*Ex, [rm, rm2])

def std_from_raw_moment(rm:RawMoment):
    assert isinstance(rm, RawMoment)
    rm2 = RawMoment(lambda x: (rm.f(x))**2)
    return CompoundMoment(lambda Ex, Ex2: (Ex2 - Ex*Ex).sqrt(), [rm, rm2])


mean       = RawMoment(lambda x: x)
#Pointwise raw second moment.
mean2      = RawMoment(t.square)
#E[x x^T], where x is a vector
mean_log   = RawMoment(t.log)
mean_log1m = RawMoment(lambda x: t.log(1-x))
var        = var_from_raw_moment(mean)
mean_recip = RawMoment(lambda x: 1/x)

moments_func2name = {
    mean       : 'mean',
    mean2      : 'mean2',
    mean_log   : 'mean_log',
    mean_log1m : 'mean_log1m',
    mean_recip : 'mean_recip'
}

def vec_square(x):
    return x[..., :, None] @ x[..., None, :]
mean_xxT   = RawMoment(vec_square)
cov_x      = CompoundMoment(lambda Ex, ExxT: ExxT - vec_square(Ex), [mean, mean_xxT])


def uniformise_moment_args(args):
    """
    moment can be called in a bunch of different ways.  For a single variable/set of variables:
    * `sample.moments("a", Mean)`
    * `sample.moments(("a", "b"), Cov)`

    For multiple variables, you can pass in a list
    sample.moments([
        "a": Mean,
        ("a", "b"): Cov
    ])

    This function converts all these argument formats into a uniform dictionary, mapping tuples of input variables to tuples of moments.
    """
    assert isinstance(args, tuple)

    mom_args_exception = Exception(".moment must be called as ...")

    #Converts everthing to a list.
    if   1 == len(args):
        args = args[0]
        if not isinstance(args, (list, tuple)):
            raise mom_args_exception
    elif 2 == len(args):
        args = [(args[0], args[1])]
    else:
        raise mom_args_exception

    result = []
    for (k, v) in args:
        if not isinstance(k, (tuple, str)):
            raise mom_args_exception
        if not isinstance(v, Moment):
            raise mom_args_exception

        if not isinstance(k, tuple):
            k = (k,)

        result.append((k, v))

    return result


def postproc_moment_outputs(result, raw_moms):
    #If we weren't given a list, we should just return a value, _not_ a list.
    if 2==len(raw_moms):
        assert 1 == len(result)
        result = result[0]
    return result


def torchdim_moments_mixin(self, *args, **kwargs):
    """
    _moments_uniform_input takes very structured input.  Must be list[tuple[str], Moment], where the tuple[str] is the variable names.
    This function allows more flexible inputs.
    Specifically, we add it to a class using:
    class ...
        _moments = torchdim_moments_mixin

    Now, you can call the _moments method in the class much more flexibly,
    sample._moments([
        "a": Mean,
        ("a", "b"): Cov
    ])
    sample._moments('a', Mean)

    Note that _moments returns torchdim tensors, whereas moments returns named tensors

    **kwargs is for e.g. computation_strategy in sample.moments(), but that doesn't currently work
    """
    moms = uniformise_moment_args(args)
    result = self._moments_uniform_input(moms, **kwargs)
    return postproc_moment_outputs(result, args)

def named_moments_mixin(self, *args, **kwargs):
    moms = uniformise_moment_args(args)
    result = self._moments_uniform_input(moms, **kwargs)
    result = [dim2named_tensor(x) for x in result]
    return postproc_moment_outputs(result, args)

def moments2raw_moments(moments: list[tuple[str], Moment]):
    raw_moments = []
    for varnames, moment in moments:
        assert isinstance(varnames, tuple)
        assert isinstance(moment, Moment)

        for raw_moment in moment.raw_moments():
            raw_moments.append((varnames, raw_moment))
    return raw_moments



