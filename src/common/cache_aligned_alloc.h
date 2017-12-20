/**
 * Allocate memory aligned on a boundary. Boundary is a power of two.
 * 
 * @author Aleksandar Dragojevic
 */

#ifndef SMABS_CACHE_ALIGNED_ALLOC_H_
#define SMABS_CACHE_ALIGNED_ALLOC_H_

#include <stdint.h>
#include <stdlib.h>

#include "constants.h"
#include "alloc.h"

template<uintptr_t BOUNDARY, class MM>
void *malloc_aligned(size_t size) {
    size_t actual_size = size + BOUNDARY + sizeof(void *);
    uintptr_t mem_block = (uintptr_t)MM::Malloc(actual_size);
    uintptr_t ret = ((mem_block + sizeof(void *) + BOUNDARY - 1) & ~(BOUNDARY - 1));
    void **back_ptr = (void **)(ret - sizeof(void *));
    *back_ptr = (void *)mem_block;
    return (void *)ret;		
}

template<class MM>
void free_aligned(void *ptr) {
    void **back_ptr = (void **)((uintptr_t)ptr - sizeof(void *));
    MM::Free(*back_ptr);
}

inline void *cache_aligned_alloc(size_t size) {
    return malloc_aligned<CACHE_LINE_SIZE_BYTES, Alloc>(size);
}

inline void cache_aligned_free(void *ptr) {
    free_aligned<Alloc>(ptr);
}

inline size_t round_to_cache_line_size(size_t size) {
    return (size + CACHE_LINE_SIZE_BYTES - 1) & ~(CACHE_LINE_SIZE_BYTES - 1);
}

inline void *cache_size_aligned_alloc(size_t size) {
    return malloc_aligned<CACHE_LINE_SIZE_BYTES, Alloc>(round_to_cache_line_size(size));
}

#endif /* SMABS_CACHE_ALIGNED_ALLOC_H_ */
