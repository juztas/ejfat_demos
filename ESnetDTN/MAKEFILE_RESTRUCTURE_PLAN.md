# Makefile Restructure Plan

## Current Situation

**Problem:**
- `Makefile.ssh` is invoked from `ESnetDTN/` directory
- It SSHs to remote nodes and runs: `cd ~/ejfat_demos/perlmutter && make -f ../scripts/Makefile.local <target>`
- `Makefile.local` expects to run from the `perlmutter/` directory where the scripts (`receive`, `send`, etc.) exist
- This hardcodes the `perlmutter/` directory path

**Current flow:**
```
ESnetDTN/ (working directory)
  ├── Makefile.ssh invoked here
  └── SSH to remote → cd perlmutter/ → Makefile.local executes there
```

## Proposed Restructure Plan

### Goal
Make `Makefile.local` work in the same directory structure where `Makefile.ssh` is invoked (i.e., `ESnetDTN/` or `runs/test1/`), so both Makefiles can operate from the same location.

### Key Changes Required

1. **Script Location Handling**
   - `Makefile.local` currently assumes scripts (`receive`, `send`, `monitor`, etc.) are in the current directory
   - Need to make script paths configurable or relocate scripts to a common location
   - Option A: Add a `SCRIPT_DIR` variable that points to where the scripts live
   - Option B: Copy/symlink scripts to each run directory
   - Option C: Modify scripts to be location-independent

2. **INSTANCE_URI File Location**
   - Currently `INSTANCE_URI_FILE ?= INSTANCE_URI` assumes current directory
   - Already configurable, but need to ensure SSH commands pass the correct path

3. **Configuration File Paths**
   - `ESnetDTN/` has config files: `receiver_config.yaml`, `sender_config.yaml`, etc.
   - `perlmutter/` also has its own scripts and configs
   - Need to decide which directory structure to use as the template

4. **Update Makefile.ssh**
   - Remove `cd ~/ejfat_demos/perlmutter` from SSH commands
   - Instead, use a variable like `REMOTE_WORK_DIR` that defaults to the same directory structure as local
   - Pass `SCRIPT_DIR` to `Makefile.local` to tell it where scripts are located

5. **Update Makefile.local**
   - Add `SCRIPT_DIR` variable with default value
   - Update all script invocations to use `$(SCRIPT_DIR)/receive`, `$(SCRIPT_DIR)/send`, etc.
   - Ensure paths work whether invoked locally or via SSH

6. **Update Makefile.common**
   - Add `SCRIPT_DIR` configuration
   - Potentially add `CONFIG_DIR` for configuration files
   - Keep `INSTANCE_URI_FILE` as already implemented (it's already flexible)

### Recommended Approach

**Approach: Add SCRIPT_DIR variable and make scripts path-independent**

```makefile
# In Makefile.common
SCRIPT_DIR ?= $(MAKEFILE_DIR)../perlmutter
CONFIG_DIR ?= .

# In Makefile.local - update script calls
receive :
    @bash -c 'export EJFAT_URI="$(INSTANCE_URI)"; ... $(SCRIPT_DIR)/receive'

# In Makefile.ssh - update to use configurable work directory
receive :
    ssh -t $(NODE) 'cd $(REMOTE_WORK_DIR) && make -f $(MAKEFILE_PATH) receive SCRIPT_DIR="$(REMOTE_SCRIPT_DIR)" ...'
```

### Benefits
- `Makefile.local` can be invoked from any directory (ESnetDTN/, runs/test1/, etc.)
- Scripts remain in their original location (perlmutter/)
- Configuration files stay with each run directory
- Backward compatible with existing usage
- SSH invocations become more flexible

### Testing Strategy
1. Test local execution from ESnetDTN/
2. Test local execution from runs/test1/
3. Test SSH execution targeting different work directories
4. Verify INSTANCE_URI file handling
5. Verify configuration file loading

## Implementation Steps

1. Update `Makefile.common` to add `SCRIPT_DIR` and `CONFIG_DIR` variables
2. Update `Makefile.local` to use `$(SCRIPT_DIR)/` prefix for all script invocations
3. Update `Makefile.ssh` to:
   - Add `REMOTE_WORK_DIR` variable
   - Remove hardcoded `cd ~/ejfat_demos/perlmutter`
   - Pass `SCRIPT_DIR` to remote Makefile.local invocations
4. Test all scenarios listed in Testing Strategy
5. Update documentation to reflect new usage patterns
