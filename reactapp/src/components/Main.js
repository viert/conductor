import React, { Component } from 'react'
import { Route } from 'react-router-dom'
import './Main.css'

import AppSidebar from './AppSidebar'
import ProjectList from './Projects/ProjectList'
import ProjectEditor from './Projects/ProjectEditor'
import GroupList from './Groups/GroupList'
import DatacenterList from './Datacenters/DatacenterList'
import { AlertBox } from '../library/AlertBox'

class Structure extends Component {
    render() {
        return (
            <div className="main">
                <AppSidebar />
                <div className="content">
                    <AlertBox />
                    <Route exact path="/projects" component={ProjectList} />
                    <Route path="/projects/:id" component={ProjectEditor} />
                    <Route exact path="/groups" component={GroupList} />
                    <Route exact path="/datacenters" component={DatacenterList} />
                </div>
            </div>
        )
    }
}

export default Structure;