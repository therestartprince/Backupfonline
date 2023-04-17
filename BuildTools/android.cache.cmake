# CMake initial cache

if( NOT DEFINED "ENV{FO_ENGINE_ROOT}" )
	message( FATAL_ERROR "Define FO_ENGINE_ROOT" )
endif()
if( NOT DEFINED "ENV{ANDROID_NDK}" )
	message( FATAL_ERROR "Define ANDROID_NDK" )
endif()
if( NOT DEFINED "ENV{ANDROID_ABI}" )
	message( FATAL_ERROR "Define ANDROID_ABI" )
endif()
if( NOT DEFINED "ENV{ANDROID_NATIVE_API_LEVEL_NUMBER}" )
	message( FATAL_ERROR "Define ANDROID_NATIVE_API_LEVEL_NUMBER" )
endif()

set( CMAKE_TOOLCHAIN_FILE "$ENV{ANDROID_NDK}/build/cmake/android.toolchain.cmake" CACHE PATH "Forced by FOnline" FORCE )
set( CMAKE_MAKE_PROGRAM "make" CACHE PATH "Forced by FOnline" FORCE )
set( ANDROID YES CACHE STRING "Forced by FOnline" FORCE )
set( ANDROID_ABI $ENV{ANDROID_ABI} CACHE STRING "Forced by FOnline" FORCE )
set( ANDROID_NATIVE_API_LEVEL "android-$ENV{ANDROID_NATIVE_API_LEVEL_NUMBER}" CACHE STRING "Forced by FOnline" FORCE )
set( ANDROID_STL "c++_static" CACHE STRING "Forced by FOnline" FORCE )
set( ANDROID_TOOLCHAIN_NAME "standalone-clang" CACHE STRING "Forced by FOnline" FORCE )
