<!-- The button to open modal -->
<label for="my-modal-3" class="btn modal-button">Config</label>

<!-- Put this part before </body> tag -->
<input type="checkbox" id="my-modal-3" class="modal-toggle" />
<div class="modal">
    <div class="modal-box relative">
        <label for="my-modal-3" class="btn btn-sm btn-circle absolute right-2 top-2">✕</label>
        <div class="form-control w-full max-w-xs">
            <label class="label">
                <span class="label-text">Game</span>
            </label>
            <input type="text" placeholder="Current Game" class="input input-bordered" />
        </div>
        <label class="btn modal-button">Save</label>
        <div class="form-control w-full max-w-xs">
            <label class="label">
                <span class="label-text">Event</span>
            </label>
            <input type="text" placeholder="Current Event" class="input input-bordered" />
        </div>
        <label class="btn modal-button">Save</label>
        <div class="form-control w-full max-w-xs">
            <label class="label">
                <span class="label-text">Field Orientation</span>
            </label>
            <select class="select select-bordered w-full max-w-xs">
                <option>Red Alliance</option>
                <option>Blue Alliance</option>
            </select>
            <label class="btn modal-button">Save</label>
            <div class="form-control w-full max-w-xs">
                <label class="label">
                    <span class="label-text">Dev Mode</span>
                </label>
                <select class="select select-bordered w-full max-w-xs">
                    <option>On</option>
                    <option>Off</option>
                </select>
                <label class="btn modal-button">Save</label>
                <div class="form-control w-full max-w-xs">
                    <label class="label">
                        <span class="label-text">Scheduling Method</span>
                    </label>
                    <select class="select select-bordered w-full max-w-xs">
                        <option>Block Scheduling</option>
                        <option>Round Robin</option>
                    </select>
                    <label class="btn modal-button">Save</label>
                </div>
            </div>
        </div>
    </div>
</div>
