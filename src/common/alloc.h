/**
 * @author Aleksandar Dragojevic aleksandar.dragojevic@epfl.ch
 *
 */

#ifndef SMABS_ALLOC_H_
#define SMABS_ALLOC_H_

#include <stdlib.h>

class Alloc {
    public:
        static void *Malloc(size_t size) {
            return ::malloc(size);
        }

        static void Free(void *ptr) {
            ::free(ptr);
        }
};

class SMABSAlloced {
public:
    void* operator new(size_t size) {
        return Alloc::Malloc(size);
    }
    
    void* operator new[](size_t size) {
        return Alloc::Malloc(size);
    }
    
    void operator delete(void* ptr) {
        Alloc::Free(ptr);
    }
    
    void operator delete[](void *ptr) {
        return Alloc::Free(ptr);
    }		
};	

#endif /* SMABS_ALLOC_H_ */
