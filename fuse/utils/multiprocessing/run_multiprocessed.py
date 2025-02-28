from typing import Any, List, Optional, Tuple
from tqdm import tqdm,trange
import multiprocessing as mp
from termcolor import cprint
import os
from collections.abc import Iterable
import inspect

'''
global dictionary that stores arguments to a new created process
Direct access is not allowed - use get_from_global_storage to access it from a worker function.

call the following "private" functions only if you know what you're doing: _store_in_global_storage, _remove_from_global_storage

Typically, you'd only need to call get_from_global_storage from your worker_func, and call run_multiprocessed and provide copy_global_storage to it, 
    with a dict of values that you want accesible from the worker_func.
'''
_multiprocess_global_storage = {}

def __orig__run_multiprocessed(worker_func, args_list, workers=0, verbose=0, 
    copy_to_global_storage: Optional[dict] = None,
    keep_results_order:bool=True,
    ) -> List[Any]:
    '''
    Args:
        worker_func: a worker function, must accept only a single positional argument and no optional args.
            For example:
            def some_worker(args):
                speed, height, banana = args
                ...
                return ans
        args_list: a list in which each element is the input to func
        workers: number of processes to use. Use 0 for no spawning of processes (helpful when debugging)
        copy_to_global_storage: Optional - to optimize the running time - the provided dict will be stored in a way that is accesible to worker_func.                    
         calling get_from_global_storage(...) will allow access to it from within any worker_func
        This allows to create a significant speedup in certain cases, and the main idea is that it allows to drastically reduce the amount of data
         that gets (automatically) pickled by python's multiprocessing library.
        Instead of copying it for each worker_func invocation, it will be copied once, upon worker process initialization.

    Returns:
        List of results from calling func, in the same order as args_list
    '''
    if 'DEBUG_SINGLE_PROCESS' in os.environ and os.environ['DEBUG_SINGLE_PROCESS'] in ['T','t','True','true',1]:
        workers = None
        cprint('Due to the env variable DEBUG_SINGLE_PROCESS being set, run_multiprocessed is not using multiprocessing','red')
    assert callable(worker_func)
    
    if verbose<1:
        tqdm_func = lambda x: x
    else:
        tqdm_func = tqdm

    if copy_to_global_storage is None:
        copy_to_global_storage = {}

    all_res = []
    if workers is None or workers<=1:        
        _store_in_global_storage(copy_to_global_storage)
        for i in tqdm_func(range(len(args_list))):
            curr_ans = worker_func(args_list[i])
            all_res.append(curr_ans)        
        _remove_from_global_storage(list(copy_to_global_storage.keys()))
    else:
        assert isinstance(workers, int)
        assert workers>=0

        with mp.Pool(processes=workers, initializer=_store_in_global_storage, initargs=(copy_to_global_storage,), maxtasksperchild=400) as pool:
            if verbose>0:
                cprint(f'multiprocess pool created with {workers} workers.', 'cyan')            
            map_func = pool.imap if keep_results_order else pool.imap_unordered
            for curr_ans in tqdm_func(map_func(
                    worker_func,
                    args_list), total=len(args_list), smoothing=0.1, disable=verbose<1):
                all_res.append(curr_ans)

    return all_res

def run_multiprocessed(worker_func, args_list, workers=0, verbose=0, 
    copy_to_global_storage: Optional[dict] = None,
    keep_results_order:bool=True,
    as_iterator=False,
    ) -> List[Any]:
    '''
    Args:
        worker_func: a worker function, must accept only a single positional argument and no optional args.
            For example:
            def some_worker(args):
                speed, height, banana = args
                ...
                return ans
        args_list: a list in which each element is the input to func
        workers: number of processes to use. Use 0 for no spawning of processes (helpful when debugging)
        copy_to_global_storage: Optional - to optimize the running time - the provided dict will be stored in a way that is accesible to worker_func.                    
         calling get_from_global_storage(...) will allow access to it from within any worker_func
        This allows to create a significant speedup in certain cases, and the main idea is that it allows to drastically reduce the amount of data
         that gets (automatically) pickled by python's multiprocessing library.
        Instead of copying it for each worker_func invocation, it will be copied once, upon worker process initialization.
        keep_results_order: determined if imap or imap_unordered is used. if strict_answers_order is set to False, then results will be ordered by their readiness.
         if strict_answers_order is set to True, the answers will be provided at the same order as defined in the args_list
        as_iterator: if True, a lightweight iterator is returned. This is useful in the cases that the entire returned answer doesn't fit in memory.
         or in the case that you want to parallelize some calculation with the generation.
         if False, the answers will be accumulated to a list and returned.


    Returns:
        if as_iterator is set to True, returns an iterator. 
        Otherwise, returns a list of results from calling func
    '''

    iter = _run_multiprocessed_as_iterator_impl(
        worker_func=worker_func,
        args_list=args_list,
        workers=workers,
        verbose=verbose,
        copy_to_global_storage=copy_to_global_storage,
        keep_results_order=keep_results_order,
    )

    if as_iterator:
        return iter
    
    ans = [x for x in iter]
    return ans


def _run_multiprocessed_as_iterator_impl(worker_func, args_list, workers=0, verbose=0, 
    copy_to_global_storage: Optional[dict] = None,
    keep_results_order:bool=True,
    ) -> List[Any]:
    '''
    an iterator version of run_multiprocessed - useful when the accumulated answer is too large to fit in memory
    
    Args:
        worker_func: a worker function, must accept only a single positional argument and no optional args.
            For example:
            def some_worker(args):
                speed, height, banana = args
                ...
                return ans
        args_list: a list in which each element is the input to func
        workers: number of processes to use. Use 0 for no spawning of processes (helpful when debugging)
        copy_to_global_storage: Optional - to optimize the running time - the provided dict will be stored in a way that is accesible to worker_func.                    
            calling get_from_global_storage(...) will allow access to it from within any worker_func
        This allows to create a significant speedup in certain cases, and the main idea is that it allows to drastically reduce the amount of data
            that gets (automatically) pickled by python's multiprocessing library.
        Instead of copying it for each worker_func invocation, it will be copied once, upon worker process initialization.
        keep_results_order: determined if imap or imap_unordered is used. if strict_answers_order is set to False, then results will be ordered by their readiness.
            if strict_answers_order is set to True, the answers will be provided at the same order as defined in the args_list
    '''
    if 'DEBUG_SINGLE_PROCESS' in os.environ and os.environ['DEBUG_SINGLE_PROCESS'] in ['T','t','True','true',1]:
        workers = None
        cprint('Due to the env variable DEBUG_SINGLE_PROCESS being set, run_multiprocessed is not using multiprocessing','red')
    assert callable(worker_func)
    
    if verbose<1:
        tqdm_func = lambda x: x
    else:
        tqdm_func = tqdm

    if copy_to_global_storage is None:
        copy_to_global_storage = {}

    if workers is None or workers<=1:        
        _store_in_global_storage(copy_to_global_storage)
        try:
            for i in tqdm_func(range(len(args_list))):
                curr_ans = worker_func(args_list[i])
                yield curr_ans
        except:
            raise
        finally:
            _remove_from_global_storage(list(copy_to_global_storage.keys()))
    else:
        assert isinstance(workers, int)
        assert workers>=0

        with mp.Pool(processes=workers, initializer=_store_in_global_storage, initargs=(copy_to_global_storage,), maxtasksperchild=400) as pool:
            if verbose>0:
                cprint(f'multiprocess pool created with {workers} workers.', 'cyan')            
            map_func = pool.imap if keep_results_order else pool.iunordered
            for curr_ans in tqdm_func(map_func(
                    worker_func,
                    args_list), total=len(args_list), smoothing=0.1, disable=verbose<1):
                yield curr_ans


def _store_in_global_storage(store_me: dict) -> None:
    """
    Copy elements to new pool processes to optimize the running time
    The arguments will be added to a global dictionary multiprocess_copied_args
    :param kwargs: list of tuples - each tuple is a key-value pair and will be added to the global dictionary
    :return: None
    """
    if store_me is None:
        return
    
    global _multiprocess_global_storage

    # making sure there are no name conflicts
    for key, _ in store_me.items():
        assert key not in _multiprocess_global_storage, f"run_multiprocessed - two multiprocessing pools with num_workers=0 are running simultaneously and using the same argument name {key}"

    _multiprocess_global_storage.update(store_me)


def _remove_from_global_storage(remove_me: List) -> None:
    """
    remove copied args for multiprocess 
    :param kwargs: list of tuples - each tuple is a key-value pair and will be added to the global dictionary
    :return: None
    """
    if remove_me is None:
        return

    global _multiprocess_global_storage
    for key in remove_me:
        del _multiprocess_global_storage[key]

def get_from_global_storage(key: str) -> Any:
    """
    Get args copied by run_multiprocessed
    """
    global _multiprocess_global_storage
    return _multiprocess_global_storage[key]