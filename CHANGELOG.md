# CHANGELOG

<!-- version list -->

## v0.7.1 (2025-12-15)

### Bug Fixes

- **test**: Resolve output filename conflict in test_output_default_extension
  ([`5971a60`](https://github.com/apathetic-tools/zipbundler/commit/5971a601a065717aa8cf009d6453520e8d70ef6e))


## v0.7.0 (2025-12-15)

### Features

- **bases**: Implement DEFAULT_SOURCE_BASES and DEFAULT_INSTALLED_BASES for directory discovery
  ([`2de4060`](https://github.com/apathetic-tools/zipbundler/commit/2de4060107157cbbcd4091cde0c6e76ac598c4b6))

- **color**: Implement color override settings with CLI flags and config support
  ([`b86a7f0`](https://github.com/apathetic-tools/zipbundler/commit/b86a7f07056fcf1de218d8fac69ec190809452dd))

- **compat**: Implement --compat flag and reorganize tests
  ([`6ee658e`](https://github.com/apathetic-tools/zipbundler/commit/6ee658ea3624edc8d259dca8d310e635eafc3d2a))

- **compress**: Implement compress boolean option with CLI flags and config support
  ([`ca0ad92`](https://github.com/apathetic-tools/zipbundler/commit/ca0ad92e02bfcaa03d73084f90baca415af21f65))

- **constants**: Implement and integrate DEFAULT_OUT_DIR, DEFAULT_DRY_RUN, and
  DEFAULT_USE_PYPROJECT_METADATA
  ([`f653044`](https://github.com/apathetic-tools/zipbundler/commit/f6530442805daf318c45ecf64729b0ced173489f))

- **constants**: Implement DEFAULT_MAIN_MODE and DEFAULT_MAIN_NAME with CLI, config, and validation
  support
  ([`cb1e0fb`](https://github.com/apathetic-tools/zipbundler/commit/cb1e0fb46109de99e2b5d89a2bb6a86512960660))

- **metadata**: Implement cascading metadata priority with DEFAULT_LICENSE_FALLBACK
  ([`d6d9556`](https://github.com/apathetic-tools/zipbundler/commit/d6d9556c76786c6df274a5d410e467169b749a5e))

- **no-main**: Implement --no-main CLI flag and insert_main config option
  ([`f9e16ea`](https://github.com/apathetic-tools/zipbundler/commit/f9e16ea1dbb0547b0c2d3ea5fa671302e41e9b7c))

- **zip-includes**: Implement type:zip support for composing builds from pre-built modules
  ([`9828479`](https://github.com/apathetic-tools/zipbundler/commit/982847949498f2017cc6aeb44abe0d3e9c331bed))

### Refactoring

- **utils**: Reorganize utils into focused submodules
  ([`2de4060`](https://github.com/apathetic-tools/zipbundler/commit/2de4060107157cbbcd4091cde0c6e76ac598c4b6))

### Testing

- Cleanup trivial, redundant, and brittle tests
  ([`dd83f0f`](https://github.com/apathetic-tools/zipbundler/commit/dd83f0f228e4170b764eaa29f28e788d09e71288))

- **build**: Add comprehensive tests for --disable-build-timestamp feature
  ([`5bf0b3a`](https://github.com/apathetic-tools/zipbundler/commit/5bf0b3a9da5bbcb40688cbf445128f42676fe2b8))

- **gitignore**: Add comprehensive test coverage for gitignore feature
  ([`2fb9092`](https://github.com/apathetic-tools/zipbundler/commit/2fb90921bc3172af25fc96cd41a16646b6d1fef5))

- **runtime-mode**: Mark test files to run only in package mode for serger compatibility
  ([`650b7c9`](https://github.com/apathetic-tools/zipbundler/commit/650b7c972f78887343d25ce8d383486d7bcb1c11))


## v0.6.0 (2025-12-15)

### Features

- **build-timestamp**: Implement --disable-build-timestamp for deterministic builds
  ([`6dd168f`](https://github.com/apathetic-tools/zipbundler/commit/6dd168f4b1c3a69241986c6e85ba657475192508))


## v0.5.0 (2025-12-15)

### Features

- **gitignore**: Implement --gitignore/--no-gitignore option aligned with serger
  ([`1050132`](https://github.com/apathetic-tools/zipbundler/commit/10501325cd14dd105d9a5ce51aa8c22d31b32674))


## v0.4.0 (2025-12-14)

### Features

- **exclude**: Align exclude handling with serger's path semantics
  ([`1415d51`](https://github.com/apathetic-tools/zipbundler/commit/1415d51deb8aacd92f430ea9dc6c5a40f28d375a))


## v0.3.0 (2025-12-14)

### Documentation

- Add --add-include documentation and examples
  ([`56b86e8`](https://github.com/apathetic-tools/zipbundler/commit/56b86e87bcbebeeee907e10a66da1debd0d83f0e))

### Features

- **add-include**: Implement --add-include CLI flag for appending includes
  ([`1309ab4`](https://github.com/apathetic-tools/zipbundler/commit/1309ab4da9029b1d4372e38dcddcbea939e8a82f))

- **include**: Align --include and config includes with serger's path semantics
  ([`3138bb2`](https://github.com/apathetic-tools/zipbundler/commit/3138bb2f85a53ed5527cee1deb97986f4fc18ba0))


## v0.2.1 (2025-12-14)

### Bug Fixes

- **config**: Fix pyproject.toml discovery to skip invalid files
  ([`83bb3a6`](https://github.com/apathetic-tools/zipbundler/commit/83bb3a6ff96c4b318b46bb37c55945a1098fd5cd))


## v0.2.0 (2025-12-14)

### Bug Fixes

- Remove duplicate main.py to resolve serger build collision
  ([`ade21ad`](https://github.com/apathetic-tools/zipbundler/commit/ade21ad91adaedf999b8701976ee7f346ad99717))

### Chores

- Add AI guidance rules and update build infrastructure
  ([`4512620`](https://github.com/apathetic-tools/zipbundler/commit/45126203daee6a19f63196fa7044209398cc5982))

- Add trove-classifiers dependency for classifier validation
  ([`8218b54`](https://github.com/apathetic-tools/zipbundler/commit/8218b54c663142eab1ad45b7b336fb535bbbaade))

### Features

- Add --dry-run mode to preview bundling without creating zip
  ([`05a42c3`](https://github.com/apathetic-tools/zipbundler/commit/05a42c3acf8a9b2b4e27eab25f497a3491edb651))

- Add --packages CLI argument to override config packages
  ([`59e3d99`](https://github.com/apathetic-tools/zipbundler/commit/59e3d992246cbfcf8dc30d20eef3a24c857b6936))

- Add CLI argument hinting for mistyped options
  ([`b3403cc`](https://github.com/apathetic-tools/zipbundler/commit/b3403cc8652f9eef1a5ca196f254b61d6849f35b))

- Add compression level support for deflate compression
  ([`17c786f`](https://github.com/apathetic-tools/zipbundler/commit/17c786fc58a748e2e582c8ee5e5dc8ca2ccbba87))

- Add configurable output directory support
  ([`724e72f`](https://github.com/apathetic-tools/zipbundler/commit/724e72ff4e5ad06b8341bb11c8bd2fbc2f59ac2e))

- Add dependency resolution for installed packages
  ([`2e5721b`](https://github.com/apathetic-tools/zipbundler/commit/2e5721b88b6d840c588539eb61786a5d6945df9a))

- Add support for listing files from archive files
  ([`027d312`](https://github.com/apathetic-tools/zipbundler/commit/027d312f001f67d4008848ac637e75cad5550622))

- Auto-detect entry_point from pyproject.toml in init command
  ([`9fc2bf5`](https://github.com/apathetic-tools/zipbundler/commit/9fc2bf54363044b504968b688b8a1e9b4e16be41))

- Auto-detect metadata from pyproject.toml in init command
  ([`232ab34`](https://github.com/apathetic-tools/zipbundler/commit/232ab34af327c4c8a762b6f607cc047f4533da34))

- Display metadata in --info command
  ([`49587e4`](https://github.com/apathetic-tools/zipbundler/commit/49587e492fdb9eebcaf0dd54fae6152b0fdfa80c))

- Implement --info flag for zipapp-style CLI
  ([`fefdca7`](https://github.com/apathetic-tools/zipbundler/commit/fefdca7c3a6c59b6db41878a0a0a8ed782b8d3c5))

- Implement automatic package discovery in zipapp-style CLI
  ([`3e6a7e5`](https://github.com/apathetic-tools/zipbundler/commit/3e6a7e509df4675d4e758df760f42a916f4cc0b4))

- Implement build command with config file support
  ([`ba8ec4b`](https://github.com/apathetic-tools/zipbundler/commit/ba8ec4b20c20aa3e9b7b320273467172ccc789a9))

- Implement exclude patterns for file filtering
  ([`1ef9d90`](https://github.com/apathetic-tools/zipbundler/commit/1ef9d90db1ba1adc6845ce89dcc2e0f02574d3ad))

- Implement incremental builds
  ([`07b40ea`](https://github.com/apathetic-tools/zipbundler/commit/07b40eadcd8dd635de11259c0617f53178c2ce13))

- Implement init command to create default config file
  ([`5713b33`](https://github.com/apathetic-tools/zipbundler/commit/5713b3393d3bd2afb853660a1f859b798034587f))

- Implement list command and remove backwards compatibility
  ([`7a81dd8`](https://github.com/apathetic-tools/zipbundler/commit/7a81dd8ca7205b4935e06f70bfee47bdcb1fa7dc))

- Implement main guard control for entry points
  ([`c8a3da7`](https://github.com/apathetic-tools/zipbundler/commit/c8a3da76458cbc671f0e2468aa80a0299fa3095d))

- Implement metadata preservation with PKG-INFO
  ([`235bd5d`](https://github.com/apathetic-tools/zipbundler/commit/235bd5daee92a8a8d0f1a0734391968d5775b583))

- Implement output.name to generate default path
  ([`291f24b`](https://github.com/apathetic-tools/zipbundler/commit/291f24b073850bfb902170e6478c099ec1adab81))

- Implement preset library for init command
  ([`067538d`](https://github.com/apathetic-tools/zipbundler/commit/067538d632fe49ae12691e60d4ec0a228f1813ab))

- Implement programmatic API
  ([`2fe5d07`](https://github.com/apathetic-tools/zipbundler/commit/2fe5d075c6f42cfbecd815622e8dfc4571b2b89a))

- Implement validate command for configuration files
  ([`dd575c2`](https://github.com/apathetic-tools/zipbundler/commit/dd575c2fc33d82d690f6798462e2658ee58aea0b))

- Implement watch mode for automatic rebuilds
  ([`4ac6e32`](https://github.com/apathetic-tools/zipbundler/commit/4ac6e327e670aeeb641854d9eba1151c495a6966))

- Search parent directories for config files
  ([`7166ffa`](https://github.com/apathetic-tools/zipbundler/commit/7166ffa631123edad1dcc0657d912496c1313718))

- Support reading existing .pyz archives as SOURCE in zipapp-style CLI
  ([`d6e28c0`](https://github.com/apathetic-tools/zipbundler/commit/d6e28c0b18e2ac04b4f0d15dc233cbee1d6192d6))

### Refactoring

- Extract argument definitions into _setup_parser() function
  ([`f3357dd`](https://github.com/apathetic-tools/zipbundler/commit/f3357dd1a43415fb95255be5aa5b5b7cc99677dd))

- Restructure CLI following serger pattern
  ([`f54f696`](https://github.com/apathetic-tools/zipbundler/commit/f54f6969282a7aee8eaae263a9955955e7393fba))

- Use apathetic-utils load_toml for TOML config loading
  ([`852b6ed`](https://github.com/apathetic-tools/zipbundler/commit/852b6edbf6798ce22ee9dbe932daf01bc582779c))

- Use apathetic_utils functions where useful
  ([`bef82d9`](https://github.com/apathetic-tools/zipbundler/commit/bef82d9e91b607eaad03fb2156a51d305eb981f2))


## v0.1.0 (2025-12-03)

- Initial Release
