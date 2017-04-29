import React, { Component } from 'react'
import PropTypes from 'prop-types'
import '../Form.css';
import ConfirmButton from '../common/ConfirmButton'

export default class GroupForm extends Component {
    constructor(props) {
        super(props)
        this.state = {
            group: props.group
        }
    }

    handleFieldChange(e) {
        let group = this.state.group;
        switch (e.target.id) {
            case "inputGroupName":
                group.name = e.target.value;
                break;
            case "inputGroupDesc":
                group.description = e.target.value;
                break;
            default:
                break;
        }
        this.setState({
            group: group
        })
    }


    handleSubmit(e) {
        e.preventDefault();
        this.props.onSubmit(this.state.group);
    }

    handleDestroy(e) {
        e.preventDefault();
        this.props.onDestroy(this.state.group)
    }

    render() {
        return (
            <form onChange={this.handleFieldChange.bind(this)} onSubmit={this.handleSubmit.bind(this)} className="form-horizontal object-form">
                <h3 className="object-form_title">Group Properties</h3>
                <div className="form-group">
                    <label htmlFor="inputGroupName" className="col-sm-3 control-label">
                        Name:
                    </label>
                    <div className="col-sm-9">
                        <input ref="firstInput" type="text" value={this.state.group.name} id="inputGroupName" className="form-control" placeholder="Group name" />
                    </div>
                </div>
                <div className="form-group">
                    <label htmlFor="inputGroupDesc" className="col-sm-3 control-label">
                        Description:
                    </label>
                    <div className="col-sm-9">
                        <input type="text" value={this.state.group.description} id="inputGroupDesc" className="form-control" placeholder="Description" />
                    </div>
                </div>
                <div className="form-group">
                    <div className="col-sm-9 col-sm-offset-3 form-buttons">
                        <button type="submit" className="btn btn-primary">Save</button>
                        { this.props.isNew ? '': <ConfirmButton onClick={this.handleDestroy.bind(this)} className="btn btn-danger">Destroy</ConfirmButton> }
                    </div>
                </div>
            </form> 
        )
    }
}

GroupForm.propTypes = {
    isNew: PropTypes.bool.isRequired,
    group: PropTypes.shape({
        name: PropTypes.string,
        description: PropTypes.string,
        project_name: PropTypes.string,
        tags: PropTypes.array
    }),
    onSubmit: PropTypes.func.isRequired,
    onDestroy: PropTypes.func.isRequired
}