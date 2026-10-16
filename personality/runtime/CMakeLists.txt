cmake_minimum_required(VERSION 3.16)

project(sherman_personality_runtime LANGUAGES C CXX)

if(NOT TARGET sherman_emotion)
  add_subdirectory(../emotion emotion)
endif()
set_target_properties(sherman_emotion PROPERTIES POSITION_INDEPENDENT_CODE ON)

add_library(sherman_personality_runtime STATIC
  src/policy.cpp
  src/routine.cpp
  src/runtime.cpp
)
target_include_directories(sherman_personality_runtime PUBLIC include)
target_link_libraries(sherman_personality_runtime PUBLIC sherman_emotion)
target_compile_features(sherman_personality_runtime PUBLIC cxx_std_17)
set_target_properties(sherman_personality_runtime PROPERTIES
  POSITION_INDEPENDENT_CODE ON
)

add_library(sherman_personality_c SHARED src/runtime_c.cpp)
target_include_directories(sherman_personality_c PUBLIC include)
target_link_libraries(sherman_personality_c PRIVATE sherman_personality_runtime)
target_compile_features(sherman_personality_c PRIVATE cxx_std_17)
set_target_properties(sherman_personality_c PROPERTIES
  OUTPUT_NAME sherman_personality_c
)

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(sherman_personality_runtime PRIVATE
    -Wall -Wextra -Wpedantic -Werror
  )
  target_compile_options(sherman_personality_c PRIVATE
    -Wall -Wextra -Wpedantic -Werror
  )
endif()

include(CTest)
if(BUILD_TESTING)
  add_executable(sherman_personality_runtime_tests tests/runtime_test.cpp)
  target_link_libraries(sherman_personality_runtime_tests
    PRIVATE sherman_personality_runtime
  )
  target_compile_features(sherman_personality_runtime_tests PRIVATE cxx_std_17)

  add_executable(sherman_personality_c_tests tests/runtime_c_test.c)
  target_link_libraries(sherman_personality_c_tests PRIVATE sherman_personality_c)
  set_target_properties(sherman_personality_c_tests PROPERTIES LINKER_LANGUAGE CXX)

  if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(sherman_personality_runtime_tests PRIVATE
      -Wall -Wextra -Wpedantic -Werror
    )
  endif()
  if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(sherman_personality_c_tests PRIVATE
      -Wall -Wextra -Wpedantic -Werror
    )
  endif()

  add_test(NAME sherman_personality_runtime_tests
           COMMAND sherman_personality_runtime_tests)
  add_test(NAME sherman_personality_c_tests COMMAND sherman_personality_c_tests)
endif()
