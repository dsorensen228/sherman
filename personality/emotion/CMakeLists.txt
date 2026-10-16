cmake_minimum_required(VERSION 3.16)

project(sherman_emotion LANGUAGES CXX)

add_library(sherman_emotion STATIC
  src/emotion.cpp
)
target_include_directories(sherman_emotion PUBLIC include)
target_compile_features(sherman_emotion PUBLIC cxx_std_17)

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(sherman_emotion PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

include(CTest)
if(BUILD_TESTING)
  add_executable(sherman_emotion_tests tests/emotion_test.cpp)
  target_link_libraries(sherman_emotion_tests PRIVATE sherman_emotion)
  if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(sherman_emotion_tests PRIVATE -Wall -Wextra -Wpedantic -Werror)
  endif()
  add_test(NAME sherman_emotion_tests COMMAND sherman_emotion_tests)
endif()
