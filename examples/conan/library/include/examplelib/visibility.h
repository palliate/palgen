#pragma once

#if defined _WIN32 || defined __CYGWIN__

  #ifdef EXPORT_SYMBOLS
    #define EXPORTED __declspec(dllexport)
  #else
      #define EXPORTED __declspec(dllimport)
  #endif

#else

  #define EXPORTED __attribute__ ((visibility ("default")))

#endif
