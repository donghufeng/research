/**
 * Copyright (c) Huawei Technologies Co., Ltd. 2023. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "math/operators/utils.h"

namespace operators {
bool KeyCompare::operator()(const key_t& a, const key_t& b) const {
    if (a.size() == b.size() && a.size() == 1) {
        return a[0] < b[0];
    }
    if (a.size() < b.size()) {
        return true;
    } else if (a.size() == b.size()) {
        return std::lexicographical_compare(a.begin(), a.end(), b.begin(), b.end());
    } else {
        return false;
    }
}
}  // namespace operators
