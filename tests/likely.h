#ifndef __LIKELY_H
#define __LIKELY_H

#define likely(x)     __builtin_expect(!!(x),1)

#endif
