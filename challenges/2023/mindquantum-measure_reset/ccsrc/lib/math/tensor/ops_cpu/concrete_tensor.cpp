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

#include "math/tensor/ops_cpu/concrete_tensor.h"

#include "math/tensor/traits.h"

namespace tensor::ops::cpu {
Tensor zeros(size_t len, TDtype dtype) {
    auto data = reinterpret_cast<void*>(calloc(len, bit_size(dtype)));
    return {dtype, TDevice::CPU, data, len};
}

Tensor ones(size_t len, TDtype dtype) {
    switch (dtype) {
        case TDtype::Float32:
            return ones<TDtype::Float32>(len);
        case TDtype::Float64:
            return ones<TDtype::Float64>(len);
        case TDtype::Complex64:
            return ones<TDtype::Complex64>(len);
        case TDtype::Complex128:
            return ones<TDtype::Complex128>(len);
    }
    return Tensor();
}
}  // namespace tensor::ops::cpu
